import sys
import inspect
import json
import pytest
from datetime import datetime, date

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


def test__format():
    my_logger = logger.Logger()
    message = {'FILE': __file__.split('/')[-1],'METHOD': inspect.stack()[0][3], 'NOW': datetime.now()}
    formatted = my_logger._format(message)
    assert formatted == json.dumps(message, indent=4, cls=logger.DateTimeEncoder)
    message = {'FILE': __file__.split('/')[-1],'METHOD': inspect.stack()[0][3], 'CLASS': logger.Logger()}
    formatted = my_logger._format(message)


def test_wrappers():
    # This test only verifies wrapper methods run without error,
    # I have no way to capture the actual logged messages.
    # kinda lame
    #
    # probably I should just write my own logger
    my_logger = logger.Logger('debug')
    errors = []
    message = 'blee'
    try:
        my_logger.debug('blee')
        my_logger.info('blee')
        my_logger.warning('blee')
        my_logger.error('blee')
        my_logger.critical('blee')
        my_logger.exception('blee')
    except:
        errors.append(sys.exc_info()[0])
    assert len(errors) == 0
