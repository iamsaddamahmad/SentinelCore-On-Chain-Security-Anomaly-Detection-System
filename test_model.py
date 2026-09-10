import pytest

from ml_detector import MLAnomalyDetector


@pytest.fixture(scope="module")
def detector():
    d = MLAnomalyDetector()
    d.load()
    return d


NORMAL_TX = {
    'Sent tnx': 10,
    'Received Tnx': 5,
    'Number of Created Contracts': 0,
    'Unique Received From Addresses': 3,
    'Unique Sent To Addresses': 2,
    'min value received': 0.1,
    'max value received ': 0.5,
    'avg val received': 0.3,
    'min val sent': 0.05,
    'max val sent': 0.2,
    'avg val sent': 0.1,
    'total transactions (including tnx to create contract': 15,
    'total Ether sent': 1.5,
    'total ether received': 0.8,
    'total ether balance': 0.3
}

WASH_TRADING_TX = {
    'Sent tnx': 5000,
    'Received Tnx': 5000,
    'Number of Created Contracts': 0,
    'Unique Received From Addresses': 3,
    'Unique Sent To Addresses': 3,
    'min value received': 0.01,
    'max value received ': 0.01,
    'avg val received': 0.01,
    'min val sent': 0.01,
    'max val sent': 0.01,
    'avg val sent': 0.01,
    'total transactions (including tnx to create contract': 10000,
    'total Ether sent': 50.0,
    'total ether received': 50.0,
    'total ether balance': 0.0
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


def test_wash_trading_pattern_flagged_as_anomaly(detector):
    result = detector.predict(WASH_TRADING_TX)
    assert result['is_anomaly'] == True
