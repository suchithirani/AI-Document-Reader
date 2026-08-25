from unittest.mock import MagicMock, patch

from app.common.utils.datetime import utc_now
from app.common.utils.pdf import get_pdf_page_count
from app.common.utils.request import get_request_info


def test_pdf_page_count():
    with patch("app.common.utils.pdf.PdfReader") as MockReader:
        mock_instance = MagicMock()
        mock_instance.pages = [MagicMock(), MagicMock(), MagicMock()]
        MockReader.return_value = mock_instance

        count = get_pdf_page_count("dummy.pdf")
        assert count == 3


def test_get_request_info():
    mock_req = MagicMock()
    mock_req.client.host = "192.168.1.1"
    mock_req.headers.get.return_value = "Chrome/120.0"

    ip, ua = get_request_info(mock_req)
    assert ip == "192.168.1.1"
    assert ua == "Chrome/120.0"


def test_datetime_utc_now():
    now = utc_now()
    assert now is not None
