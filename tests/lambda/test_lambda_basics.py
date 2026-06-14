"""Basic Lambda invocation tests."""

import json


def test_echo_handler_returns_payload_unchanged(lambda_client, lambda_factory) -> None:
    """Deploy the echo handler and verify it returns the invocation payload unchanged."""
    file_path = 'lambdas/echo_handler.py'
    handler = 'handler'
    payload = {'name': 'Avshalom'}

    function_name = lambda_factory(file_path, handler)

    response = lambda_client.invoke(
        FunctionName=function_name,
        Payload=json.dumps(payload).encode(),
    )

    assert response['StatusCode'] == 200
    assert 'FunctionError' not in response

    received_payload = json.loads(response['Payload'].read())
    assert received_payload['echoed'] == payload
