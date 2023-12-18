from loguru import logger
from plum import bigendian, littleendian
from plum.bigendian import uint8
from plum.bytes import BytesX
from plum.str import StrX
from plum.structure import Structure, member, sized_member
from plum.utilities import pack, pack_and_dump


class ArtDmxPacketPlum(Structure):
    """
    Structure representing an ArtDMX packet
    (https://art-net.org.uk/how-it-works/streaming-packets/artdmx-packet-definition/)
    """

    # ArtNet packet identifier
    id: str = member(
        fmt=StrX(name="cstring", encoding="ascii", nbytes=8, zero_termination=True),
        default="Art-Net",
        readonly=True,
    )
    # ArtDMX OpCode
    opcode: int = member(fmt=littleendian.uint16, default=0x5000, readonly=True)
    # ArtNet protocol version (14)
    protocol_version: int = member(fmt=bigendian.uint16, default=14, readonly=True)
    # Sequence number to indicate the order of packets.
    # 0 means not implemented
    sequence: int = member(fmt=uint8, default=0)
    # Number between 0 and 3 that defines the physical port that generated the packet.
    # (Purely informative)
    physical_port: int = member(fmt=uint8, default=0)
    # Low 8 bits of port address that specify the universe
    universe: int = member(fmt=uint8)
    # High 8 bits of port address that specify the subnet (MSB not used)
    subnet: int = member(fmt=uint8, default=0)
    # 16 bit number defining the number of bytes encoded in the data field
    length: int = member(fmt=bigendian.uint16)
    # The bytes representing the DMX channels
    data: bytes = sized_member(fmt=BytesX(), size=length)


class ArtDmxPacket(ArtDmxPacketPlum):
    """
    Structure representing an ArtDMX packet
    (https://art-net.org.uk/how-it-works/streaming-packets/artdmx-packet-definition/)
    """

    def __init__(self, **args):
        args["length"] = len(args["data"])
        super().__init__(**args)

    def get_bytes(self) -> bytes:
        return pack(self)

    def output_data(self):
        buffer, dump = pack_and_dump(self)
        logger.debug(buffer)
        logger.debug(dump)
