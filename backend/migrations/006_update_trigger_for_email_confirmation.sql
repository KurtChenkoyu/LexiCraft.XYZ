-- Migration: Update Trigger for Email Confirmation Tracking
-- Created: 2024-12-04
-- Description: Updates handle_new_user trigger to track email confirmation status

-- Update the trigger function to include email confirmation tracking
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
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
    COALESCE(NEW.email_confirmed, FALSE), -- Get confirmation status from auth.users
    CASE WHEN COALESCE(NEW.email_confirmed, FALSE) = TRUE THEN NOW() ELSE NULL END
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
EXCEPTION
  WHEN others THEN
    RAISE WARNING 'Error in handle_new_user: %', SQLERRM;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Update the user update function to sync email confirmation status
CREATE OR REPLACE FUNCTION public.handle_user_update()
RETURNS trigger AS $$
BEGIN
  UPDATE public.users
  SET 
    email = NEW.email,
    email_confirmed = COALESCE(NEW.email_confirmed, email_confirmed),
    email_confirmed_at = CASE 
      WHEN NEW.email_confirmed = TRUE AND email_confirmed_at IS NULL 
      THEN NOW() 
      ELSE email_confirmed_at 
    END,
    updated_at = NOW()
  WHERE id = NEW.id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Add trigger to update email confirmation when auth.users.email_confirmed changes
DROP TRIGGER IF EXISTS on_auth_user_email_confirmed ON auth.users;
CREATE TRIGGER on_auth_user_email_confirmed
  AFTER UPDATE ON auth.users
  FOR EACH ROW
  WHEN (OLD.email_confirmed IS DISTINCT FROM NEW.email_confirmed)
  EXECUTE FUNCTION public.handle_user_update();


