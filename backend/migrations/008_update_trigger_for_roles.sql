-- Migration: Update Trigger to Assign Default Role
-- Created: 2024
-- Description: Updates handle_new_user trigger to assign default 'learner' role

-- Update the trigger function to assign default 'learner' role
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  -- Insert user record
  INSERT INTO public.users (
    id, 
    email, 
    name, 
    country, 
    created_at, 
    updated_at, 
    email_confirmed, 
    email_confirmed_at
  )
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'name', NEW.raw_user_meta_data->>'full_name', ''),
    COALESCE(NEW.raw_user_meta_data->>'country', 'TW'),
    NOW(),
    NOW(),
    COALESCE(NEW.email_confirmed, FALSE),
    CASE WHEN COALESCE(NEW.email_confirmed, FALSE) = TRUE THEN NOW() ELSE NULL END
  )
  ON CONFLICT (id) DO NOTHING;
  
  -- Assign default 'learner' role (can be changed during onboarding)
  INSERT INTO public.user_roles (user_id, role, created_at)
  VALUES (NEW.id, 'learner', NOW())
  ON CONFLICT (user_id, role) DO NOTHING;
  
  RETURN NEW;
EXCEPTION
  WHEN others THEN
    RAISE WARNING 'Error in handle_new_user: %', SQLERRM;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

