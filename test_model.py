import pytest

from ml_detector import MLAnomalyDetector


@pytest.fixture(scope="module")
def detector():
    d = MLAnomalyDetector(chain_key="ethereum")
    d.load()
    return d


NORMAL_TX = {
    'value_eth': 0.5,
    'gas_price_gwei': 20.0,
    'gas': 21000,
    'gas_used': 21000,
    'input_length': 0,
    'is_contract': 0,
    'success': 1,
}

SUSPICIOUS_TX = {
    'value_eth': 500.0,
    'gas_price_gwei': 300.0,
    'gas': 5000000,
    'gas_used': 4800000,
    'input_length': 2000,
    'is_contract': 1,
    'success': 1,
}


def test_model_loads(detector):
    assert detector.model is not None


def test_predict_returns_expected_keys(detector):
    result = detector.predict(NORMAL_TX)
    assert 'is_anomaly' in result
    assert 'score' in result
    assert 'confidence' in result


def test_normal_transaction_has_confidence_score(detector):
    result = detector.predict(NORMAL_TX)
    assert 0.0 <= result['confidence'] <= 1.0


def test_suspicious_transaction_flagged_as_anomaly(detector):
    result = detector.predict(SUSPICIOUS_TX)
    assert result['is_anomaly']
