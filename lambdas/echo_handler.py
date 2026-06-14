"""Lambda handler that echoes back the received event."""


def handler(event, context):
    """Return the incoming event wrapped under the 'echoed' key."""
    return {'echoed': event}
