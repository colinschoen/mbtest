# encoding=utf-8
import logging

import requests
from brunns.matchers.html import has_title
from brunns.matchers.object import between
from brunns.matchers.response import response_with
from contexttimer import Timer
from hamcrest import assert_that, is_, has_entry

from mbtest.imposters import Imposter, Proxy, Stub, Predicate
from mbtest.matchers import had_request

logger = logging.getLogger(__name__)


def test_proxy(mock_server):
    imposter = Imposter(Proxy(to="http://example.com"))

    with mock_server(imposter) as server:
        response = requests.get("{0}/".format(imposter.url))

        assert_that(response, is_(response_with(status_code=200, body=has_title("Example Domain"))))
        assert_that(server, had_request(path="/", method="GET"))


def test_proxy_in_stub(mock_server):
    imposter = Imposter(Stub(responses=Proxy(to="http://example.com")))

    with mock_server(imposter):
        response = requests.get("{0}/".format(imposter.url))

        assert_that(response, is_(response_with(status_code=200, body=has_title("Example Domain"))))


def test_proxy_delay(mock_server):
    imposter = Imposter(Stub(responses=Proxy(to="http://example.com", wait=500)))

    with mock_server(imposter), Timer() as t:
        requests.get("{0}/".format(imposter.url))

    assert_that(
        t.elapsed, between(0.5, 0.9)
    )  # Slightly longer than the wait time, to give example.com and the 'net time to work.


def test_inject_headers(mock_server):
    target_imposter = Imposter(Stub(Predicate(path="/test")))
    with mock_server(target_imposter) as server:
        proxy_imposter = Imposter(
            Stub(
                responses=Proxy(
                    to=target_imposter.url,
                    inject_headers={"X-Clacks-Overhead": "GNU Terry Pratchett"},
                )
            )
        )
        server.add_imposters(proxy_imposter)

        requests.get(proxy_imposter.url / "test")
        assert_that(
            server,
            had_request(
                path="/test", headers=has_entry("X-Clacks-Overhead", "GNU Terry Pratchett")
            ),
        )


def test_structure_to():
    expected_proxy = Proxy("http://darwin.dog")
    proxy_structure = expected_proxy.as_structure()
    proxy = Proxy.from_structure(proxy_structure)
    assert proxy.to == expected_proxy.to


def test_structure_wait():
    expected_proxy = Proxy("http://darwin.dog", wait=200)
    proxy_structure = expected_proxy.as_structure()
    proxy = Proxy.from_structure(proxy_structure)
    assert proxy.wait == expected_proxy.wait


def test_structure_inject_headers():
    expected_proxy = Proxy(
        "http://darwin.dog", inject_headers={"X-Clacks-Overhead": "GNU Terry Pratchett"}
    )
    proxy_structure = expected_proxy.as_structure()
    proxy = Proxy.from_structure(proxy_structure)
    assert proxy.inject_headers == expected_proxy.inject_headers
