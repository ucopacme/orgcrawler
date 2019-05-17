import os
import inspect
import json
import boto3
from datetime import datetime, date
import pytest

from orgcrawler import logger


def test_DateTimeEncoder():
    dte = logger.DateTimeEncoder()
    today = dte.default(date.today())
    assert isinstance(today, str)
    now = dte.default(datetime.now())
    assert isinstance(now, str)
    with pytest.raises(TypeError):
        serial = dte.default("stringy thing")


def test_Logger():
    my_logger = logger.Logger()
    assert my_logger.log.getEffectiveLevel() == 30
    my_logger = logger.Logger('error')
    assert my_logger.log.getEffectiveLevel() == 40
    print(my_logger.log.hasHandlers())


def test__format():
    my_logger = logger.Logger()
    message = {'FILE': __file__.split('/')[-1],'METHOD': inspect.stack()[0][3], 'NOW': datetime.now()}
    formatted = my_logger._format(message)
    print(formatted)
    assert formatted == json.dumps(message, indent=4, cls=logger.DateTimeEncoder)
    message = {'FILE': __file__.split('/')[-1],'METHOD': inspect.stack()[0][3], 'CLASS': logger.Logger()}
    formatted = my_logger._format(message)
    print(formatted)


