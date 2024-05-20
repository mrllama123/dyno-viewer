from boto3.session import Session


def get_available_profiles():
    return list(Session().available_profiles)


def get_all_regions():
    return Session().get_available_regions("dynamodb")
