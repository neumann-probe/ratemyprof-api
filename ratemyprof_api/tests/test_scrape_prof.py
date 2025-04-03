from ..ratemyprof_api import RateMyProfApi

uci = "1074"

def test_init_ratemyprof():
    api = RateMyProfApi(uci, testing = True)
