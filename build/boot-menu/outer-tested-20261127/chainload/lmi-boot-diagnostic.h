/* SPDX-License-Identifier: MIT
 * Included once by aboot.c. RAM-only diagnostic; no variables or disk writes.
 */
static const char *lmi_last_boot_stage="not entered";
static void lmi_console_line(const char *text){
    CHAR16 out[161];UINTN i=0;
    if(!gST||!gST->ConOut)return;
    while(text&&*text&&i<158){
        unsigned char c=(unsigned char)*text++;
        out[i++]=(c>=32&&c<127)?(CHAR16)c:L'?';
    }
    out[i++]=L'\r';out[i++]=L'\n';out[i]=0;
    gST->ConOut->OutputString(gST->ConOut,out);
}
void lmi_boot_stage(const char *stage){
    lmi_last_boot_stage=stage;
    tlog_notice("LMI boot stage: %s",stage);
}
void lmi_boot_failed(void){
    list *p;unsigned count=0;EFI_INPUT_KEY key;
    if(!gST||!gST->ConOut)return;
    /* Called only on a returned error, before ExitBootServices. */
    gST->ConOut->ClearScreen(gST->ConOut);
    gST->ConOut->EnableCursor(gST->ConOut,FALSE);
    lmi_console_line("LMI: LineageOS launch failed before handoff");
    lmi_console_line("Last attempted stage:");
    lmi_console_line(lmi_last_boot_stage);
    lmi_console_line("Recent warnings/errors (newest first):");
    for(p=list_last(logbuffer);p&&count<6;p=p->prev){
        struct log_buff *item=LIST_DATA(p,struct log_buff*);
        if(!item||item->level<LEVEL_WARNING)continue;
        lmi_console_line(item->tag);
        lmi_console_line(item->content);
        count++;
    }
    lmi_console_line("Photograph this screen. No image was flashed.");
    lmi_console_line("Volume/Power: continue; automatic return after 120 seconds.");
    if(gST->ConIn)gST->ConIn->Reset(gST->ConIn,FALSE);
    for(unsigned tick=0;tick<1200;tick++){
        if(gST->ConIn&&!EFI_ERROR(gST->ConIn->ReadKeyStroke(gST->ConIn,&key)))break;
        gBS->Stall(100000);
    }
}
