import os
import time
import binascii
from zipfile import ZipFile
from zipfile import ZipInfo
from zipfile import ZIP_STORED
from zipfile import ZIP_DEFLATED
from zipfile import ZIP64_LIMIT

try:
    import zlib  # We may need its compression method

    crc32 = zlib.crc32
except ImportError:
    zlib = None
    crc32 = binascii.crc32


class WZipFile(ZipFile):
    def writeobj(self, file_object, file_length, arcname, compress_type=None, date_time=None):
        """Put the bytes from file_object into the archive under the name
                arcname."""
        if not self.fp:
            raise RuntimeError(
                "Attempt to write to ZIP archive that was already closed")

        arcname = os.path.normpath(os.path.splitdrive(arcname)[1])
        while arcname[0] in (os.sep, os.altsep):
            arcname = arcname[1:]
        date_time = date_time if date_time else time.localtime(time.time())[:6]
        zinfo = ZipInfo(arcname, date_time)
        zinfo.external_attr = zinfo.external_attr = 0o600 << 16  # Unix attributes
        zinfo.compress_type = compress_type if compress_type else self.compression

        zinfo.file_size = file_length
        zinfo.flag_bits = 0x00
        zinfo.header_offset = self.fp.tell()  # Start of header bytes

        self._writecheck(zinfo)
        self._didModify = True

        # Must overwrite CRC and sizes with correct data later
        zinfo.CRC = crc = 0
        zinfo.compress_size = compress_size = 0
        # Compressed size can be larger than uncompressed size
        zip64 = self._allowZip64 and \
                zinfo.file_size * 1.05 > ZIP64_LIMIT
        self.fp.write(zinfo.FileHeader(zip64))
        if zinfo.compress_type == ZIP_DEFLATED:
            cmpr = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION,
                                    zlib.DEFLATED, -15)
        else:
            cmpr = None
        file_size = 0
        while 1:
            buf = file_object.read(1024 * 8)
            if not buf:
                break
            file_size += len(buf)
            crc = crc32(buf, crc) & 0xffffffff
            if cmpr:
                buf = cmpr.compress(buf)
                compress_size += len(buf)
            self.fp.write(buf)
        if cmpr:
            buf = cmpr.flush()
            compress_size += len(buf)
            self.fp.write(buf)
            zinfo.compress_size = compress_size
        else:
            zinfo.compress_size = file_size
        zinfo.CRC = crc
        zinfo.file_size = file_size
        if not zip64 and self._allowZip64:
            if file_size > ZIP64_LIMIT:
                raise RuntimeError('File size has increased during compressing')
            if compress_size > ZIP64_LIMIT:
                raise RuntimeError('Compressed size larger than uncompressed size')
        # Seek backwards and write file header (which will now include
        # correct CRC and file sizes)
        position = self.fp.tell()  # Preserve current position in file
        self.fp.seek(zinfo.header_offset, 0)
        self.fp.write(zinfo.FileHeader(zip64))
        self.fp.seek(position, 0)
        self.filelist.append(zinfo)
        self.NameToInfo[zinfo.filename] = zinfo


if __name__ == '__main__':
    zipfile = WZipFile('/tmp/test1.zip', 'w', ZIP_STORED, allowZip64=True)
    try:
        with open('/tmp/123.log', 'rb') as f:
            st = os.stat('/tmp/123.log')
            file_length = st.st_size
            date_time = time.localtime(st.st_mtime)[0:6]
            zipfile.writeobj(f, file_length, 'abc/123.log', date_time=date_time)
        with open('/tmp/adb.log', 'rb') as f:
            st = os.stat('/tmp/adb.log')
            file_length = st.st_size
            date_time = time.localtime(st.st_mtime)[0:6]
            zipfile.writeobj(f, file_length, 'abc/adb.log', date_time=date_time)
    finally:
        zipfile.close()
