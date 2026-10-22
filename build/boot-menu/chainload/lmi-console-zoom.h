/* SPDX-License-Identifier: MIT
 * Render the existing HII bitmap font at 2x without changing panel resolution.
 */
#ifndef LMI_CONSOLE_ZOOM_H
#define LMI_CONSOLE_ZOOM_H
#include <Protocol/GraphicsOutput.h>
#include <Protocol/HiiFont.h>
#include <Library/MemoryAllocationLib.h>
static EFI_GRAPHICS_OUTPUT_PROTOCOL *lmi_zoom_gop;
static EFI_HII_FONT_PROTOCOL *lmi_zoom_font;
static UINTN lmi_zoom_columns,lmi_zoom_y,lmi_zoom_bottom;
static BOOLEAN lmi_zoom_ready;
static void lmi_pixels_double(const EFI_GRAPHICS_OUTPUT_BLT_PIXEL *src,
                             EFI_GRAPHICS_OUTPUT_BLT_PIXEL *dst,UINTN w,UINTN h){
    UINTN x,y;
    for(y=0;y<h;y++)for(x=0;x<w;x++){
        EFI_GRAPHICS_OUTPUT_BLT_PIXEL p=src[y*w+x];
        dst[(y*2)*(w*2)+x*2]=p;dst[(y*2)*(w*2)+x*2+1]=p;
        dst[(y*2+1)*(w*2)+x*2]=p;dst[(y*2+1)*(w*2)+x*2+1]=p;
    }
}
static BOOLEAN lmi_zoom_init(void){
    static EFI_GUID gop_guid=EFI_GRAPHICS_OUTPUT_PROTOCOL_GUID;
    static EFI_GUID font_guid=EFI_HII_FONT_PROTOCOL_GUID;
    EFI_GRAPHICS_OUTPUT_BLT_PIXEL black={0};UINTN w,h;
    if(EFI_ERROR(gBS->LocateProtocol(&gop_guid,NULL,(VOID**)&lmi_zoom_gop))||
       EFI_ERROR(gBS->LocateProtocol(&font_guid,NULL,(VOID**)&lmi_zoom_font))||
       !lmi_zoom_gop||!lmi_zoom_font||!lmi_zoom_gop->Mode||!lmi_zoom_gop->Mode->Info)return FALSE;
    w=lmi_zoom_gop->Mode->Info->HorizontalResolution;
    h=lmi_zoom_gop->Mode->Info->VerticalResolution;
    if(w<320||h<228||w>8192||h>8192)return FALSE;
    lmi_zoom_columns=(w-32)/16;lmi_zoom_y=38;
    lmi_zoom_bottom=38+((h-76)/38)*38;
    if(EFI_ERROR(lmi_zoom_gop->Blt(lmi_zoom_gop,&black,EfiBltVideoFill,0,0,0,0,w,h,0)))return FALSE;
    lmi_zoom_ready=TRUE;return TRUE;
}
static BOOLEAN lmi_zoom_line(CHAR16 *line){
    EFI_IMAGE_OUTPUT small,*image=&small;
    EFI_GRAPHICS_OUTPUT_BLT_PIXEL *pixels,*large;EFI_STATUS status;
    UINTN w,h=19,bytes,screen_width;
    if(!lmi_zoom_ready)return FALSE;
    w=lmi_zoom_columns*8;bytes=w*h*sizeof(*pixels);
    pixels=AllocateZeroPool(bytes);large=AllocateZeroPool(bytes*4);
    if(!pixels||!large){if(pixels)FreePool(pixels);if(large)FreePool(large);return FALSE;}
    ZeroMem(&small,sizeof(small));small.Width=(UINT16)w;small.Height=(UINT16)h;small.Image.Bitmap=pixels;
    status=lmi_zoom_font->StringToImage(lmi_zoom_font,
        EFI_HII_OUT_FLAG_CLIP|EFI_HII_IGNORE_LINE_BREAK|EFI_HII_IGNORE_IF_NO_GLYPH,
        line,NULL,&image,0,0,NULL,NULL,NULL);
    if(EFI_ERROR(status)||image!=&small||small.Image.Bitmap!=pixels){
        /* The pinned HII renderer must honor a caller-supplied bitmap. */
        FreePool(pixels);FreePool(large);return FALSE;
    }
    lmi_pixels_double(pixels,large,w,h);FreePool(pixels);
    screen_width=lmi_zoom_gop->Mode->Info->HorizontalResolution;
    if(lmi_zoom_y+38>lmi_zoom_bottom){
        status=lmi_zoom_gop->Blt(lmi_zoom_gop,NULL,EfiBltVideoToVideo,0,76,0,38,screen_width,lmi_zoom_bottom-76,0);
        if(EFI_ERROR(status)){FreePool(large);return FALSE;}
        lmi_zoom_y=lmi_zoom_bottom-38;
    }
    /* The full opaque row already contains its black background. Clearing
     * the visible row first exposes a blank frame and adds a panel update. */
    status=lmi_zoom_gop->Blt(lmi_zoom_gop,large,EfiBltBufferToVideo,0,0,16,lmi_zoom_y,w*2,h*2,w*2*sizeof(*large));
    FreePool(large);
    if(EFI_ERROR(status))return FALSE;
    lmi_zoom_y+=38;return TRUE;
}
#endif
