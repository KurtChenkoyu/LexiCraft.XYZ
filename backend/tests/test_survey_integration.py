"""
Integration Tests for LexiSurvey Frontend → Backend → Database Flow

Tests the complete flow:
1. Start survey session
2. Submit answers
3. Verify session persistence
4. Verify database records
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import text
from src.main import app
from src.database.postgres_connection import PostgresConnection
from src.database.neo4j_connection import Neo4jConnection


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def db_conn():
    """Create a database connection for testing."""
    conn = PostgresConnection()
    yield conn
    conn.close()


@pytest.fixture
def neo4j_conn():
    """Create a Neo4j connection for testing."""
    conn = Neo4jConnection()
    yield conn
    conn.close()


class TestSurveyIntegration:
    """Integration tests for the complete survey flow."""
    
    def test_start_survey_creates_session(self, client, db_conn):
        """Test that starting a survey creates a session in the database."""
        # Start survey
        response = client.post(
            "/api/v1/survey/start",
            json={"cefr_level": "B1"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "session_id" in data
        assert "status" in data
        assert data["status"] == "continue"
        assert "payload" in data
        assert "question_id" in data["payload"]
        assert "word" in data["payload"]
        assert "options" in data["payload"]
        assert len(data["payload"]["options"]) == 6
        
        session_id = data["session_id"]
        
        # Verify session exists in database
        with db_conn.get_session() as session:
            result = session.execute(
                text("""
                    SELECT id, user_id, current_rank, status, start_time
                    FROM survey_sessions
                    WHERE id = :session_id
                """),
                {"session_id": uuid.UUID(session_id)}
            )
            row = result.fetchone()
            
            assert row is not None
            assert str(row[0]) == session_id
            assert row[2] is not None  # current_rank
            assert row[3] == "active"  # status
            
            # Verify history record exists
            history_result = session.execute(
                text("""
                    SELECT history
                    FROM survey_history
                    WHERE session_id = :session_id
                """),
                {"session_id": uuid.UUID(session_id)}
            )
            history_row = history_result.fetchone()
            assert history_row is not None
            
            # Verify question record exists
            question_result = session.execute(
                text("""
                    SELECT question_id, word, rank, phase
                    FROM survey_questions
                    WHERE session_id = :session_id
                """),
                {"session_id": uuid.UUID(session_id)}
            )
            question_row = question_result.fetchone()
            assert question_row is not None
            assert question_row[1] == data["payload"]["word"]
    
    def test_submit_answer_updates_session(self, client, db_conn):
        """Test that submitting an answer updates the session state."""
        # Start survey
        start_response = client.post(
            "/api/v1/survey/start",
            json={"cefr_level": "B1"}
        )
        assert start_response.status_code == 200
        start_data = start_response.json()
        session_id = start_data["session_id"]
        question_id = start_data["payload"]["question_id"]
        
        # Get initial state
        with db_conn.get_session() as session:
            initial_result = session.execute(
                text("""
                    SELECT current_rank, status
                    FROM survey_sessions
                    WHERE id = :session_id
                """),
                {"session_id": uuid.UUID(session_id)}
            )
            initial_row = initial_result.fetchone()
            initial_rank = initial_row[0]
        
        # Submit answer (select first target option)
        target_options = [
            opt["id"] for opt in start_data["payload"]["options"]
            if opt.get("type") == "target" or "target" in opt["id"].lower()
        ]
        
        if not target_options:
            # If no target options found, select first option
            target_options = [start_data["payload"]["options"][0]["id"]]
        
        answer_response = client.post(
            "/api/v1/survey/next",
            params={"session_id": session_id},
            json={
                "question_id": question_id,
                "selected_option_ids": target_options[:1],  # Select first target
                "time_taken": 5.0
            }
        )
        
        assert answer_response.status_code == 200
        answer_data = answer_response.json()
        
        # Verify response
        assert "status" in answer_data
        assert answer_data["status"] in ["continue", "complete"]
        
        # Verify database was updated
        with db_conn.get_session() as session:
            # Check session was updated
            updated_result = session.execute(
                text("""
                    SELECT current_rank, status
                    FROM survey_sessions
                    WHERE id = :session_id
                """),
                {"session_id": uuid.UUID(session_id)}
            )
            updated_row = updated_result.fetchone()
            assert updated_row is not None
            
            # Check history was updated
            history_result = session.execute(
                text("""
                    SELECT history
                    FROM survey_history
                    WHERE session_id = :session_id
                """),
                {"session_id": uuid.UUID(session_id)}
            )
            history_row = history_result.fetchone()
            assert history_row is not None
            history = history_row[0]
            assert isinstance(history, list)
            assert len(history) >= 1
            assert "rank" in history[0]
            assert "correct" in history[0]
            assert "time_taken" in history[0]
    
    def test_survey_completes_after_minimum_questions(self, client, db_conn):
        """Test that survey completes after minimum questions and saves results."""
        # Start survey
        start_response = client.post(
            "/api/v1/survey/start",
            json={"cefr_level": "B1"}
        )
        assert start_response.status_code == 200
        start_data = start_response.json()
        session_id = start_data["session_id"]
        
        # Submit answers until completion (minimum 15 questions)
        current_data = start_data
        question_count = 0
        max_questions = 20  # Safety limit
        
        while current_data.get("status") == "continue" and question_count < max_questions:
            question_id = current_data["payload"]["question_id"]
            
            # Select target options (correct answer)
            target_options = [
                opt["id"] for opt in current_data["payload"]["options"]
                if opt.get("type") == "target" or "target" in opt["id"].lower()
            ]
            
            if not target_options:
                target_options = [current_data["payload"]["options"][0]["id"]]
            
            # Submit answer
            answer_response = client.post(
                "/api/v1/survey/next",
                params={"session_id": session_id},
                json={
                    "question_id": question_id,
                    "selected_option_ids": target_options,
                    "time_taken": 5.0
                }
            )
            
            assert answer_response.status_code == 200
            current_data = answer_response.json()
            question_count += 1
        
        # Verify survey completed
        assert current_data.get("status") == "complete"
        assert "metrics" in current_data
        assert "volume" in current_data["metrics"]
        assert "reach" in current_data["metrics"]
        assert "density" in current_data["metrics"]
        
        # Verify results were saved to database
        with db_conn.get_session() as session:
            results_result = session.execute(
                text("""
                    SELECT volume, reach, density
                    FROM survey_results
                    WHERE session_id = :session_id
                """),
                {"session_id": uuid.UUID(session_id)}
            )
            results_row = results_result.fetchone()
            assert results_row is not None
            assert results_row[0] == current_data["metrics"]["volume"]
            assert results_row[1] == current_data["metrics"]["reach"]
            assert results_row[2] == current_data["metrics"]["density"]
            
            # Verify session status is updated
            session_result = session.execute(
                text("""
                    SELECT status
                    FROM survey_sessions
                    WHERE id = :session_id
                """),
                {"session_id": uuid.UUID(session_id)}
            )
            session_row = session_result.fetchone()
            assert session_row[0] == "completed"
    
    def test_session_persistence_across_requests(self, client, db_conn):
        """Test that session state persists across multiple requests."""
        # Start survey
        start_response = client.post(
            "/api/v1/survey/start",
            json={"cefr_level": "B1"}
        )
        assert start_response.status_code == 200
        start_data = start_response.json()
        session_id = start_data["session_id"]
        question_id = start_data["payload"]["question_id"]
        
        # Submit first answer
        target_options = [
            opt["id"] for opt in start_data["payload"]["options"]
            if opt.get("type") == "target" or "target" in opt["id"].lower()
        ]
        if not target_options:
            target_options = [start_data["payload"]["options"][0]["id"]]
        
        answer_response = client.post(
            "/api/v1/survey/next",
            params={"session_id": session_id},
            json={
                "question_id": question_id,
                "selected_option_ids": target_options[:1],
                "time_taken": 5.0
            }
        )
        assert answer_response.status_code == 200
        first_answer_data = answer_response.json()
        
        # Verify history contains first answer
        with db_conn.get_session() as session:
            history_result = session.execute(
                text("""
                    SELECT history
                    FROM survey_history
                    WHERE session_id = :session_id
                """),
                {"session_id": uuid.UUID(session_id)}
            )
            history_row = history_result.fetchone()
            history = history_row[0]
            assert len(history) >= 1
            assert history[0]["question_id"] == question_id
        
        # Submit second answer (if survey continues)
        if first_answer_data.get("status") == "continue":
            second_question_id = first_answer_data["payload"]["question_id"]
            second_target_options = [
                opt["id"] for opt in first_answer_data["payload"]["options"]
                if opt.get("type") == "target" or "target" in opt["id"].lower()
            ]
            if not second_target_options:
                second_target_options = [first_answer_data["payload"]["options"][0]["id"]]
            
            second_answer_response = client.post(
                "/api/v1/survey/next",
                params={"session_id": session_id},
                json={
                    "question_id": second_question_id,
                    "selected_option_ids": second_target_options[:1],
                    "time_taken": 5.0
                }
            )
            assert second_answer_response.status_code == 200
            
            # Verify history contains both answers
            with db_conn.get_session() as session:
                history_result = session.execute(
                    text("""
                        SELECT history
                        FROM survey_history
                        WHERE session_id = :session_id
                    """),
                    {"session_id": uuid.UUID(session_id)}
                )
                history_row = history_result.fetchone()
                history = history_row[0]
                assert len(history) >= 2
                assert history[0]["question_id"] == question_id
                assert history[1]["question_id"] == second_question_id


