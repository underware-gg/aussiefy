# Retry settings

Set `retry_limit` to `3` before starting the worker. The client retries requests only after a connection failure; a rejected request is returned to the caller immediately.

The `backoff_ms` value controls the delay between attempts. Increasing it does not change the number of attempts. If `retry_limit` is `0`, the client sends the request once and returns the result.

Run `worker --check-config` to check the configuration. See [the settings reference](https://example.invalid/settings#retry_limit) for the accepted values. Keep the existing configuration file until the replacement passes this check.
