/* SPDX-License-Identifier: MIT
 * Screen-only formatting: serial/file logs retain their original text.
 */
#include <Library/UefiBootServicesTableLib.h>
static UINTN lmi_text_columns=80;
static BOOLEAN lmi_text_ready=FALSE;
static void lmi_fit_console_line(const char *text){
    CHAR16 line[258];UINTN used=1,limit,columns,rows,best=0,area=0;
    INT32 mode;
    if(!gST||!gST->ConOut||!gST->ConOut->Mode||!text)return;
    if(!lmi_text_ready){
        for(mode=0;mode<gST->ConOut->Mode->MaxMode;mode++){
            if(!EFI_ERROR(gST->ConOut->QueryMode(gST->ConOut,(UINTN)mode,&columns,&rows))&&
               columns>=20&&columns<=512&&rows>=5&&rows<=512&&columns*rows>area){
                best=(UINTN)mode;area=columns*rows;
            }
        }
        if(area)gST->ConOut->SetMode(gST->ConOut,best);
        if(!EFI_ERROR(gST->ConOut->QueryMode(gST->ConOut,(UINTN)gST->ConOut->Mode->Mode,&columns,&rows))&&columns>=4)
            lmi_text_columns=columns;
        gST->ConOut->EnableCursor(gST->ConOut,FALSE);
        lmi_text_ready=TRUE;
    }
    limit=lmi_text_columns>256?254:lmi_text_columns-2;
    line[0]=L' ';
    for(;;){
        unsigned char c=(unsigned char)*text;
        if(!c||c=='\n'||used>=limit){
            line[used++]=L'\r';line[used++]=L'\n';line[used]=0;
            gST->ConOut->OutputString(gST->ConOut,line);
            used=1;
            if(!c)break;
            if(c=='\n'){text++;continue;}
        }
        text++;
        if(c=='\r')continue;
        line[used++]=(c=='\t')?L' ':((c>=32&&c<127)?(CHAR16)c:L'?');
    }
}
