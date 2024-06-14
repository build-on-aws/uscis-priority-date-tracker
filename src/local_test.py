from handler import lambda_handler

class MockContext:
    def __init__(self):
        self.function_name = "mock_function_name"
        self.aws_request_id = "mock_aws_request_id"
        self.log_group_name = "mock_log_group_name"
        self.log_stream_name = "mock_log_stream_name"

    def get_remaining_time_in_millis(self):
        return 300000  # 5 minutes in milliseconds

mock_context = MockContext()

mock_event = {
    "key1": "value1",
    "key2": "value2",
    # Add any other relevant data for your event
}

result = lambda_handler(mock_event, mock_context)
print(result)