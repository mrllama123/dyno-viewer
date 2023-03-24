import boto3

def get_available_profiles():
    return [profile for profile in boto3.session.Session().available_profiles]
