# swarm_communicator.py

**Ne işe yarar?** Alt Jeff'ler arasında iletişim köprüsü. Mesaj gönderme, okuma, broadcast ve iletişim geçmişi sağlar.

**Nasıl çalıştırılır?**
```
python3 ~/.hermes/scripts/swarm_communicator.py send jeff_1 jeff_2 "Lead DM'leri bitti"
python3 ~/.hermes/scripts/swarm_communicator.py read jeff_2
python3 ~/.hermes/scripts/swarm_communicator.py broadcast jeff_1 tamam "İşlem bitti"
python3 ~/.hermes/scripts/swarm_communicator.py history
```

**Örnek çıktı:**
```
📨 Mesaj gönderildi: jeff_1 → jeff_2
   [bilgi] Lead DM'leri bitti
📋 İLETİŞİM GEÇMİŞİ (2 kayıt)
```

**Bağımlılıklar:** -
