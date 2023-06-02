from boto3.session import Session


def get_available_profiles():
    return [profile for profile in Session().available_profiles]


def get_all_regions():
    return Session().get_available_regions("dynamodb")
