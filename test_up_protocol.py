#!/usr/bin/env python3
"""
Test script for UP Protocol implementation
Verifies message encoding/decoding without hardware connection
"""

from network.up_protocol import UPProtocol
from utils.logger import setup_logger

logger = setup_logger()

def test_pan_tilt_command():
    print("\n=== Testing Pan/Tilt Command ===")
    protocol = UPProtocol()

    pan = 45.5
    tilt = -30.25

    message = protocol.build_pan_tilt_command(pan, tilt)

    print(f"Pan: {pan}°, Tilt: {tilt}°")
    print(f"Message length: {len(message)} bytes")
    print(f"Message (hex): {message.hex()}")

    return message

def test_position_query():
    print("\n=== Testing Position Query ===")
    protocol = UPProtocol()

    message = protocol.build_position_query()

    print(f"Query message length: {len(message)} bytes")
    print(f"Message (hex): {message.hex()}")

    return message

def test_stop_command():
    print("\n=== Testing Stop Command ===")
    protocol = UPProtocol()

    message = protocol.build_stop_command()

    print(f"Stop message length: {len(message)} bytes")
    print(f"Message (hex): {message.hex()}")

    return message

def test_message_parsing():
    print("\n=== Testing Message Parsing ===")
    protocol = UPProtocol()

    cmd_message = protocol.build_pan_tilt_command(90.0, -45.0)

    parsed = protocol.parse_message(cmd_message)

    if parsed:
        print("[PASS] Message parsed successfully")
        print(f"  Sequence: {parsed['sequence']}")
        print(f"  Command ID: {parsed['command_id']}")
        print(f"  Payload length: {parsed['payload_length']}")
        print(f"  Payload (hex): {parsed['payload'].hex()}")
    else:
        print("[FAIL] Message parsing failed")

    return parsed

def test_position_response_parsing():
    print("\n=== Testing Position Response Parsing ===")
    protocol = UPProtocol()

    import struct
    pan_value = int(123.45 * 100)
    tilt_value = int(-67.89 * 100)
    payload = struct.pack('>ii', pan_value, tilt_value)

    header = struct.pack('>HHHH', 0x5550, 1, 10, len(payload))
    message = header + payload

    checksum = protocol._calculate_crc16(message)
    message += struct.pack('>H', checksum)

    print(f"Simulated response message length: {len(message)} bytes")

    result = protocol.parse_position_response(message)

    if result:
        pan, tilt = result
        print(f"[PASS] Position parsed: Pan={pan}°, Tilt={tilt}°")
        print(f"  Expected: Pan=123.45°, Tilt=-67.89°")

        if abs(pan - 123.45) < 0.01 and abs(tilt - (-67.89)) < 0.01:
            print("  [PASS] Values match expected!")
        else:
            print("  [FAIL] Values don't match!")
    else:
        print("[FAIL] Position parsing failed")

    return result

def test_checksum_validation():
    print("\n=== Testing Checksum Validation ===")
    protocol = UPProtocol()

    message = protocol.build_pan_tilt_command(0.0, 0.0)

    parsed_valid = protocol.parse_message(message)
    print(f"Valid message: {'[PASS]' if parsed_valid else '[FAIL]'}")

    corrupted_message = bytearray(message)
    corrupted_message[-1] ^= 0xFF

    parsed_invalid = protocol.parse_message(bytes(corrupted_message))
    print(f"Corrupted message: {'[PASS] Correctly rejected' if not parsed_invalid else '[FAIL] Incorrectly accepted'}")

def main():
    print("=" * 50)
    print("UP Protocol Implementation Test Suite")
    print("=" * 50)

    try:
        test_pan_tilt_command()
        test_position_query()
        test_stop_command()
        test_message_parsing()
        test_position_response_parsing()
        test_checksum_validation()

        print("\n" + "=" * 50)
        print("All tests completed!")
        print("=" * 50)

    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
