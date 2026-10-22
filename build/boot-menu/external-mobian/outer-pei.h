/* SPDX-License-Identifier: MIT
 * Included after AddHob in the pinned MemoryInitPeiLib.c.
 * Split only the allocation HOBs; leave the MMU descriptor and FD size intact.
 */
#include "outer-range.h"
STATIC struct lmi_outer_range LmiOuter;
STATIC VOID LmiFindOuter(fdt *Fdt, UINT64 UefiBase, UINT64 UefiSize) {
  int Node, Ns=0, Ne=0; const VOID *A, *B;
  PARM_MEMORY_REGION_DESCRIPTOR_EX D;
  struct lmi_outer_range R;
  LmiOuter.start=0;
  Node=fdt_path_offset(Fdt,"/chosen");
  if(Node<0)return;
  A=fdt_getprop(Fdt,Node,"linux,initrd-start",&Ns);
  B=fdt_getprop(Fdt,Node,"linux,initrd-end",&Ne);
  if(lmi_outer_decode(A,Ns,B,Ne,&R))return;
  if(lmi_outer_overlap(&R,UefiBase,UefiSize)||
     lmi_outer_overlap(&R,0xCE000000ULL,0x02000000ULL))return;
  for(D=GetPlatformMemoryMap();D->Length;D++) {
    if(D->HobOption==AddMem&&D->ResourceType==EFI_RESOURCE_SYSTEM_MEMORY&&
       D->MemoryType==EfiConventionalMemory&&lmi_outer_within(&R,D->Address,D->Length)) {
      LmiOuter=R;return;
    }
  }
}
STATIC VOID LmiAddProtectedHob(PARM_MEMORY_REGION_DESCRIPTOR_EX D) {
  ARM_MEMORY_REGION_DESCRIPTOR_EX Part;
  if(!LmiOuter.start||!lmi_outer_overlap(&LmiOuter,D->Address,D->Length)) {
    AddHob(D);return;
  }
  /* FindOuter proved that the complete range belongs to one conventional
   * descriptor. Never create an overlapping full conventional allocation. */
  if(!lmi_outer_within(&LmiOuter,D->Address,D->Length))CpuDeadLoop();
  Part=*D;
  if(D->Address<LmiOuter.page_start) {
    Part.Length=LmiOuter.page_start-D->Address;AddHob(&Part);
  }
  Part=*D;Part.Address=LmiOuter.page_start;
  Part.Length=LmiOuter.page_end-LmiOuter.page_start;
  Part.MemoryType=EfiReservedMemoryType;AddHob(&Part);
  if(LmiOuter.page_end<D->Address+D->Length) {
    Part=*D;Part.Address=LmiOuter.page_end;
    Part.Length=D->Address+D->Length-LmiOuter.page_end;AddHob(&Part);
  }
}
