from itertools import cycle
from unittest import mock

import pytest

from bot.utils.timing import timing_handler

pytestmark = [pytest.mark.asyncio]


async def test_timing_handler():
    fn = mock.AsyncMock()
    with mock.patch('bot.utils.timing.time.time') as t:
        t.side_effect = cycle((0, 1000))
        r = await timing_handler(fn)()
        assert t.call_count == 2
        fn.assert_awaited_once_with()
        assert r == (fn.return_value, 1000 * 1e3)

        t.side_effect = cycle((0, 1500))
        r = await timing_handler(fn)(1, 2, 3)
        assert t.call_count == 4
        fn.assert_awaited_with(1, 2, 3)
        assert r == (fn.return_value, 1500 * 1e3)

        t.side_effect = cycle((0, 2000))
        fn.side_effect = ValueError('error')
        with pytest.raises(ValueError):
            r = await timing_handler(fn, should_raise=True)(4, 5, 6)
        fn.assert_awaited_with(4, 5, 6)
