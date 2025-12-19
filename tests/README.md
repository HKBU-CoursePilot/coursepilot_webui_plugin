# Module Tests

This folder contains tests for this module.

## Structure

- `test_<module_name>.py` - Unit tests (pytest)
- `conftest.py` - Shared fixtures (optional)

## Running Tests

```bash
# From project root with venv activated
pytest <module_type>/<module_name>/tests/
```

## Notes

- Tests are **optional** for lightweight modules
- For modules >200 LOC or with complex state, tests are recommended
- HyperRed will run adversarial tests separately
