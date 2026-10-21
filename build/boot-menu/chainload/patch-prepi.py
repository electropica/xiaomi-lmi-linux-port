#!/usr/bin/env python3
"""Minimal, pinned PrePi FFS3 large-file support. No build or source mutation."""
import hashlib

UPSTREAM_SHA256 = 'ad66475a52972cc455f697610076528a5dbc7285af00d1f19d287ba792103e88'
PATH = 'EmbeddedPkg/Library/PrePiLib/FwVol.c'


def patch(raw):
    assert hashlib.sha256(raw).hexdigest() == UPSTREAM_SHA256, 'Unreviewed PrePi source'
    s = raw.decode().replace('\r\n', '\n')

    def once(old, new):
        nonlocal s
        assert s.count(old) == 1, old
        s = s.replace(old, new)

    once('/**\n  Returns the highest bit set', '''/* LMI_PREPI_FFS3_V1: validate the complete header before reading ExtendedSize.
   Keep the original UINT32 traversal, rejecting overflow and truncated files. */
STATIC
BOOLEAN
LmiFfsFileLayout (
  IN EFI_FFS_FILE_HEADER *Header,
  IN UINT64 Remaining,
  OUT UINT32 *HeaderSize,
  OUT UINT32 *FileSize
  )
{
  UINT64 Length;

  if (Remaining < sizeof (EFI_FFS_FILE_HEADER)) {
    return FALSE;
  }
  *HeaderSize = IS_FFS_FILE2 (Header) ? sizeof (EFI_FFS_FILE_HEADER2) : sizeof (EFI_FFS_FILE_HEADER);
  if (Remaining < *HeaderSize) {
    return FALSE;
  }
  Length = IS_FFS_FILE2 (Header) ? ((EFI_FFS_FILE_HEADER2 *)Header)->ExtendedSize : FFS_FILE_SIZE (Header);
  if ((IS_FFS_FILE2 (Header) && ((FFS_FILE_SIZE (Header) != 0) || (Length <= 0x00FFFFFF))) ||
      (Length < *HeaderSize) || (Length > Remaining) || (Length > 0xFFFFFFF8ULL)) {
    return FALSE;
  }
  *FileSize = (UINT32)Length;
  return TRUE;
}

/**
  Returns the highest bit set''')
    once('  UINT8  Sum;\n', '  UINT8  Sum;\n  UINTN  HeaderSize;\n')
    once('  Ptr = (UINT8 *)FileHeader;\n', '  Ptr = (UINT8 *)FileHeader;\n  HeaderSize = IS_FFS_FILE2 (FileHeader) ? sizeof (EFI_FFS_FILE_HEADER2) : sizeof (EFI_FFS_FILE_HEADER);\n')
    once('Index < sizeof (EFI_FFS_FILE_HEADER) - 3', 'Index < HeaderSize - 3')
    once('Index < sizeof (EFI_FFS_FILE_HEADER); Index++', 'Index < HeaderSize; Index++')
    once('  UINT32                          FileLength;','  UINT32                          FileLength;\n  UINT32                          HeaderSize;')
    once('  FvLength = FwVolHeader->FvLength;', '''  FvLength = FwVolHeader->FvLength;
  if ((FvLength < sizeof (EFI_FIRMWARE_VOLUME_HEADER)) || (FvLength > 0xFFFFFFF8ULL)) {
    *FileHeader = NULL;
    return EFI_NOT_FOUND;
  }''')
    once('    FileLength       = *(UINT32 *)(*FileHeader)->Size & 0x00FFFFFF;', '''    if (((UINTN)*FileHeader < (UINTN)FwVolHeader) ||
        ((UINTN)*FileHeader - (UINTN)FwVolHeader > FvLength) ||
        !LmiFfsFileLayout (*FileHeader, FvLength - ((UINTN)*FileHeader - (UINTN)FwVolHeader), &HeaderSize, &FileLength)) {
      *FileHeader = NULL;
      return EFI_NOT_FOUND;
    }''')
    once('    if (FwVolHeader->ExtHeaderOffset != 0) {', '''    if (FwVolHeader->ExtHeaderOffset != 0) {
      if ((UINT64)FwVolHeader->ExtHeaderOffset + sizeof (EFI_FIRMWARE_VOLUME_EXT_HEADER) > FvLength) {
        *FileHeader = NULL;
        return EFI_NOT_FOUND;
      }''')
    once('      FfsFileHeader     = (EFI_FFS_FILE_HEADER *)(((UINT8 *)FwVolExHeaderInfo) + FwVolExHeaderInfo->ExtHeaderSize);', '''      if ((FwVolExHeaderInfo->ExtHeaderSize < sizeof (EFI_FIRMWARE_VOLUME_EXT_HEADER)) ||
          ((UINT64)FwVolHeader->ExtHeaderOffset + FwVolExHeaderInfo->ExtHeaderSize > FvLength)) {
        *FileHeader = NULL;
        return EFI_NOT_FOUND;
      }
      FfsFileHeader     = (EFI_FFS_FILE_HEADER *)(((UINT8 *)FwVolExHeaderInfo) + FwVolExHeaderInfo->ExtHeaderSize);''')
    once('    switch (FileState) {', '''    if (((FileState == EFI_FILE_DATA_VALID) || (FileState == EFI_FILE_MARKED_FOR_UPDATE) || (FileState == EFI_FILE_DELETED)) &&
        !LmiFfsFileLayout (FfsFileHeader, FvLength - FileOffset, &HeaderSize, &FileLength)) {
      *FileHeader = NULL;
      return EFI_NOT_FOUND;
    }

    switch (FileState) {''')
    assert s.count('        FileLength       = *(UINT32 *)(FfsFileHeader->Size) & 0x00FFFFFF;\n') == 2
    s = s.replace('        FileLength       = *(UINT32 *)(FfsFileHeader->Size) & 0x00FFFFFF;\n', '')
    once('  UINT32                     FileSize;', '  UINT32                     FileSize;\n  UINT32                     HeaderSize;')
    once('  Section   = (EFI_COMMON_SECTION_HEADER *)(FfsFileHeader + 1);\n  FileSize  = *(UINT32 *)(FfsFileHeader->Size) & 0x00FFFFFF;\n  FileSize -= sizeof (EFI_FFS_FILE_HEADER);', '''  if (!LmiFfsFileLayout (FfsFileHeader, 0xFFFFFFF8ULL, &HeaderSize, &FileSize)) {
    return EFI_NOT_FOUND;
  }
  Section   = (EFI_COMMON_SECTION_HEADER *)((UINT8 *)FfsFileHeader + HeaderSize);
  FileSize -= HeaderSize;''')
    once('  EFI_PEI_FV_HANDLE    VolumeHandle;','  EFI_PEI_FV_HANDLE    VolumeHandle;\n  UINT32               HeaderSize;\n  UINT32               FileSize;')
    once('  FileInfo->BufferSize     = ((*(UINT32 *)FileHeader->Size) & 0x00FFFFFF) -  sizeof (EFI_FFS_FILE_HEADER);\n  FileInfo->Buffer         = (FileHeader + 1);', '''  if (!LmiFfsFileLayout (FileHeader,
        ((EFI_FIRMWARE_VOLUME_HEADER *)VolumeHandle)->FvLength - ((UINTN)FileHeader - (UINTN)VolumeHandle),
        &HeaderSize, &FileSize)) {
    return EFI_INVALID_PARAMETER;
  }
  FileInfo->BufferSize     = FileSize - HeaderSize;
  FileInfo->Buffer         = (UINT8 *)FileHeader + HeaderSize;''')
    return s.encode()
