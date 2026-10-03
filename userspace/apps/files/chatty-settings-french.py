#!/usr/bin/env python3
"""Generate a local French-only settings overlay from installed Chatty 0.8.7-2."""
from pathlib import Path
import subprocess,xml.etree.ElementTree as ET

version=subprocess.check_output(['dpkg-query','-W','-f=${Version}','chatty'],text=True).strip()
if version!='0.8.7-2':raise SystemExit('Unsupported Chatty version: '+version)
data=subprocess.check_output(['gresource','extract','/usr/bin/chatty','/sm/puri/Chatty/ui/chatty-settings-dialog.ui'])
root=ET.fromstring(data)
if root.tag!='interface':raise SystemExit('Unexpected UI root')
root.set('domain','purism-chatty')
translations={
 'Read Receipts':'Accusés de lecture',
 'Typing Indicators':'Indicateurs de saisie',
 'Remove Tracking IDs From URLs':'Retirer les identifiants de suivi des liens',
 'Show Attachment Previews':'Afficher les aperçus des pièces jointes',
 'Convert Emoticons':'Convertir les émoticônes',
 'When you type :) it will be changed to 😃':'La saisie de :) sera remplacée par 😃',
 'Send Messages With Enter':'Envoyer les messages avec Entrée',
 'PGP Settings':'Paramètres PGP',
 'Clear Stuck SMS':'Effacer les SMS bloqués',
 'MMS Carrier Settings':'Paramètres MMS de l’opérateur',
 "Your modem's phone number":'Numéro de téléphone du modem',
 'Current PGP Key':'Clé PGP actuelle',
 'Generate Chatty PGP Key':'Générer une clé PGP pour Discussions',
 'Signing ID':'Identifiant de signature',
 'Public Key Fingerprint':'Empreinte de la clé publique',
 'Optional':'Facultatif',
 'Full Name':'Nom complet',
 'PGP ID':'Identifiant PGP',
 'PGP Passphrase':'Phrase secrète PGP',
 'No Blocked Chats':'Aucune discussion bloquée',
 'Enable Purple Accounts':'Activer les comptes Purple',
 'User ID':'Identifiant utilisateur',
}
count=0
for prop in root.findall('.//property'):
 if prop.get('translatable') in ('yes','true','True') and prop.text in translations:
  prop.text=translations[prop.text]
  prop.set('translatable','no')
  count+=1
if count<10:raise SystemExit('Unexpected UI: too few matching labels')
out=Path('/usr/local/share/lmi-chatty/ui/chatty-settings-dialog.ui')
out.parent.mkdir(parents=True,exist_ok=True)
if out.exists():raise SystemExit('Existing overlay: refusing overwrite')
ET.indent(root)
out.write_bytes(ET.tostring(root,encoding='utf-8',xml_declaration=True))
out.chmod(0o644)
wrapper=Path('/usr/local/bin/lmi-chatty-safe')
s=wrapper.read_text()
anchor='export GST_REGISTRY_1_0=$cache/registry.bin\n'
assert s.count(anchor)==1
extra='''# This optional overlay is French-only; other session languages keep upstream UI.
case "${LC_ALL:-${LC_MESSAGES:-${LANG:-}}}" in
 fr*) export G_RESOURCE_OVERLAYS=/sm/puri/Chatty/ui=/usr/local/share/lmi-chatty/ui;;
esac
'''
wrapper.write_text(s.replace(anchor,anchor+extra))
wrapper.chmod(0o755)
print('FRENCH_SETTINGS_OVERLAY_LABELS',count)
