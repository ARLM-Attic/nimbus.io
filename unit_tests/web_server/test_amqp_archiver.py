# -*- coding: utf-8 -*-
"""
test_amqp_archiver.py

test diyapi_web_server/amqp_archiver.py
"""
import os
import unittest
import uuid
import random
import time
import hashlib
import zlib

from unit_tests.util import random_string, generate_key
from unit_tests.web_server import util

from diyapi_web_server.amqp_exchange_manager import AMQPExchangeManager
from messages.archive_key_entire import ArchiveKeyEntire
from messages.archive_key_start import ArchiveKeyStart
from messages.archive_key_next import ArchiveKeyNext
from messages.archive_key_final import ArchiveKeyFinal
from messages.archive_key_start_reply import ArchiveKeyStartReply
from messages.archive_key_next_reply import ArchiveKeyNextReply
from messages.archive_key_final_reply import ArchiveKeyFinalReply

from diyapi_web_server.amqp_archiver import AMQPArchiver
from diyapi_web_server.exceptions import *


EXCHANGES = os.environ['DIY_NODE_EXCHANGES'].split()
NUM_SEGMENTS = 10


class TestAMQPArchiver(unittest.TestCase):
    """test diyapi_web_server/amqp_archiver.py"""
    def setUp(self):
        self.amqp_handler = util.FakeAMQPHandler()
        self.exchange_manager = AMQPExchangeManager(EXCHANGES)
        self._key_generator = generate_key()
        self._real_uuid1 = uuid.uuid1
        uuid.uuid1 = util.fake_uuid_gen().next
        self._real_sample = random.sample
        random.sample = util.fake_sample

    def tearDown(self):
        uuid.uuid1 = self._real_uuid1
        random.sample = self._real_sample

    def _make_small_data(self, avatar_id, timestamp, key, fail=False):
        file_size = 1024 * NUM_SEGMENTS
        file_adler32 = -42
        file_md5 = 'ffffff'
        messages = []
        messages_to_append = []
        segments = []
        for i in xrange(NUM_SEGMENTS):
            segment_number = i + 1
            segment = random_string(1024)
            segments.append(segment)
            segment_adler32 = zlib.adler32(segment)
            segment_md5 = hashlib.md5(segment).digest()
            request_id = uuid.UUID(int=i).hex
            message = ArchiveKeyEntire(
                request_id,
                avatar_id,
                self.amqp_handler.exchange,
                self.amqp_handler.queue_name,
                timestamp,
                key,
                0, # version number
                segment_number,
                file_adler32,
                file_md5,
                segment_adler32,
                segment_md5,
                segment
            )
            reply = ArchiveKeyFinalReply(
                request_id,
                ArchiveKeyFinalReply.successful,
                0
            )
            messages.append((message, self.exchange_manager[i]))
            if self.exchange_manager.is_down(i):
                for exchange in self.exchange_manager.handoff_exchanges(i):
                    if not fail:
                        self.amqp_handler.replies_to_send_by_exchange[(
                            request_id, exchange
                        )].put(reply)
                    messages_to_append.append((message, exchange))
            else:
                self.amqp_handler.replies_to_send_by_exchange[(
                    request_id, self.exchange_manager[i]
                )].put(reply)
        messages.extend(messages_to_append)
        return segments, messages, file_size, file_adler32, file_md5

    def test_archive_small(self):
        avatar_id = 1001
        timestamp = time.time()
        key = self._key_generator.next()
        (
            segments,
            messages,
            file_size,
            file_adler32,
            file_md5,
        ) = self._make_small_data(avatar_id, timestamp, key)

        archiver = AMQPArchiver(
            self.amqp_handler,
            self.exchange_manager,
            avatar_id,
            key,
            timestamp
        )
        previous_size = archiver.archive_final(
            file_size,
            file_adler32,
            file_md5,
            segments,
            0
        )

        self.assertEqual(previous_size, 0)

        expected = [
            (message.marshall(), exchange)
            for message, exchange in messages
        ]
        actual = [
            (message.marshall(), exchange)
            for message, exchange in self.amqp_handler.messages
        ]
        self.assertEqual(
            actual, expected, 'archiver did not send expected messages')

    def test_archive_small_with_handoff(self):
        avatar_id = 1001
        timestamp = time.time()
        key = self._key_generator.next()
        self.exchange_manager.mark_down(0)
        (
            segments,
            messages,
            file_size,
            file_adler32,
            file_md5,
        ) = self._make_small_data(avatar_id, timestamp, key)
        self.exchange_manager.mark_up(0)

        archiver = AMQPArchiver(
            self.amqp_handler,
            self.exchange_manager,
            avatar_id,
            key,
            timestamp
        )

        previous_size = archiver.archive_final(
            file_size,
            file_adler32,
            file_md5,
            segments,
            0
        )

        self.assertEqual(previous_size, 0)
        self.assertTrue(self.exchange_manager.is_down(0))

        expected = [
            (message.marshall(), exchange)
            for message, exchange in messages
        ]
        actual = [
            (message.marshall(), exchange)
            for message, exchange in self.amqp_handler.messages
        ]
        self.assertEqual(
            actual, expected, 'archiver did not send expected messages')

    def test_archive_small_with_failure(self):
        avatar_id = 1001
        timestamp = time.time()
        key = self._key_generator.next()
        self.exchange_manager.mark_down(0)
        (
            segments,
            messages,
            file_size,
            file_adler32,
            file_md5,
        ) = self._make_small_data(avatar_id, timestamp, key, True)
        self.exchange_manager.mark_up(0)

        archiver = AMQPArchiver(
            self.amqp_handler,
            self.exchange_manager,
            avatar_id,
            key,
            timestamp
        )

        self.assertRaises(ArchiveFailedError,
            archiver.archive_final,
            file_size,
            file_adler32,
            file_md5,
            segments,
            0
        )

        self.assertTrue(self.exchange_manager.is_down(0))

        expected = [
            (message.marshall(), exchange)
            for message, exchange in messages
        ]
        actual = [
            (message.marshall(), exchange)
            for message, exchange in self.amqp_handler.messages
        ]
        self.assertEqual(
            actual, expected, 'archiver did not send expected messages')

    def _make_large_data(self, avatar_id, timestamp, key, n_slices):
        file_size = NUM_SEGMENTS * n_slices
        file_adler32 = -42
        file_md5 = 'ffffff'
        messages = []
        messages_to_append = []
        slices = []
        segment_adler32s = {}
        segment_md5s = {}

        slices.append([])
        sequence_number = 0
        for i in xrange(NUM_SEGMENTS):
            segment_number = i + 1
            segment = random_string(1)
            slices[sequence_number].append(segment)
            segment_adler32s[segment_number] = zlib.adler32(segment)
            segment_md5s[segment_number] = hashlib.md5(segment)
            request_id = uuid.UUID(int=i).hex
            message = ArchiveKeyStart(
                request_id,
                avatar_id,
                self.amqp_handler.exchange,
                self.amqp_handler.queue_name,
                timestamp,
                sequence_number,
                key,
                0, # version number
                segment_number,
                len(segment),
                segment
            )
            reply = ArchiveKeyStartReply(
                request_id,
                ArchiveKeyStartReply.successful,
                0
            )
            messages.append((message, self.exchange_manager[i]))
            if self.exchange_manager.is_down(i):
                for exchange in self.exchange_manager.handoff_exchanges(i):
                    messages_to_append.append((message, exchange))
                    self.amqp_handler.replies_to_send_by_exchange[(
                        request_id, exchange
                    )].put(reply)
            else:
                self.amqp_handler.replies_to_send_by_exchange[(
                    request_id, self.exchange_manager[i]
                )].put(reply)

        messages.extend(messages_to_append)

        for _ in xrange(n_slices - 2):
            slices.append([])
            sequence_number += 1
            for i in xrange(NUM_SEGMENTS):
                segment_number = i + 1
                segment = random_string(1)
                slices[sequence_number].append(segment)
                segment_adler32s[segment_number] = zlib.adler32(
                    segment,
                    segment_adler32s[segment_number]
                )
                segment_md5s[segment_number].update(segment)
                request_id = uuid.UUID(int=i).hex
                message = ArchiveKeyNext(
                    request_id,
                    sequence_number,
                    segment
                )
                reply = ArchiveKeyNextReply(
                    request_id,
                    ArchiveKeyNextReply.successful,
                    0
                )
                if self.exchange_manager.is_down(i):
                    for exchange in self.exchange_manager.handoff_exchanges(i):
                        messages.append((message, exchange))
                        self.amqp_handler.replies_to_send_by_exchange[(
                            request_id, exchange
                        )].put(reply)
                else:
                    messages.append((message, self.exchange_manager[i]))
                    self.amqp_handler.replies_to_send_by_exchange[(
                        request_id, self.exchange_manager[i]
                    )].put(reply)

        slices.append([])
        sequence_number += 1
        for i in xrange(NUM_SEGMENTS):
            segment_number = i + 1
            segment = random_string(1)
            slices[sequence_number].append(segment)
            segment_adler32s[segment_number] = zlib.adler32(
                segment,
                segment_adler32s[segment_number]
            )
            segment_md5s[segment_number].update(segment)
            request_id = uuid.UUID(int=i).hex
            message = ArchiveKeyFinal(
                request_id,
                sequence_number,
                file_size,
                file_adler32,
                file_md5,
                segment_adler32s[segment_number],
                segment_md5s[segment_number].digest(),
                segment
            )
            reply = ArchiveKeyFinalReply(
                request_id,
                ArchiveKeyFinalReply.successful,
                0
            )
            if self.exchange_manager.is_down(i):
                for exchange in self.exchange_manager.handoff_exchanges(i):
                    messages.append((message, exchange))
                    self.amqp_handler.replies_to_send_by_exchange[(
                        request_id, exchange
                    )].put(reply)
            else:
                messages.append((message, self.exchange_manager[i]))
                self.amqp_handler.replies_to_send_by_exchange[(
                    request_id, self.exchange_manager[i]
                )].put(reply)

        return slices, messages, file_size, file_adler32, file_md5

    def test_archive_large(self):
        avatar_id = 1001
        timestamp = time.time()
        key = self._key_generator.next()
        (
            slices,
            messages,
            file_size,
            file_adler32,
            file_md5,
        ) = self._make_large_data(avatar_id, timestamp, key, 4)

        archiver = AMQPArchiver(
            self.amqp_handler,
            self.exchange_manager,
            avatar_id,
            key,
            timestamp
        )

        for segments in slices[:-1]:
            archiver.archive_slice(segments, 0)

        previous_size = archiver.archive_final(
            file_size,
            file_adler32,
            file_md5,
            slices[-1],
            0
        )

        self.assertEqual(previous_size, 0)

        expected = [
            (message.marshall(), exchange)
            for message, exchange in messages
        ]
        actual = [
            (message.marshall(), exchange)
            for message, exchange in self.amqp_handler.messages
        ]
        self.assertEqual(
            actual, expected, 'archiver did not send expected messages')

    def test_archive_large_with_handoff(self):
        avatar_id = 1001
        timestamp = time.time()
        key = self._key_generator.next()
        self.exchange_manager.mark_down(0)
        (
            slices,
            messages,
            file_size,
            file_adler32,
            file_md5,
        ) = self._make_large_data(avatar_id, timestamp, key, 4)
        self.exchange_manager.mark_up(0)

        archiver = AMQPArchiver(
            self.amqp_handler,
            self.exchange_manager,
            avatar_id,
            key,
            timestamp
        )

        for segments in slices[:-1]:
            archiver.archive_slice(segments, 0)

        previous_size = archiver.archive_final(
            file_size,
            file_adler32,
            file_md5,
            slices[-1],
            0
        )

        self.assertEqual(previous_size, 0)

        expected = [
            (message.marshall(), exchange)
            for message, exchange in messages
        ]
        actual = [
            (message.marshall(), exchange)
            for message, exchange in self.amqp_handler.messages
        ]
        self.assertEqual(
            actual, expected, 'archiver did not send expected messages')


if __name__ == "__main__":
    from diyapi_tools.standard_logging import initialize_logging
    _log_path = "/var/log/pandora/test_web_server.log"
    initialize_logging(_log_path)
    unittest.main()
