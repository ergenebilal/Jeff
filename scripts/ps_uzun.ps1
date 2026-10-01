# Test betigi — daemon'un stdout yakalama davranisini anlamak icin.
# Asagidaki yorum satirlari sadece betigi uzatmak amaciyla eklenmistir.
# Amac: calisan ve calismayan scriptler arasindaki fark uzunluk mu?
# Deneme 1: bu betik oncekinden belirgin sekilde uzun olacak.
# Deneme 2: ayni islevi gormeli, sadece daha fazla yorum icermeli.
# Deneme 3: eger bu calisirsa, kisayolu cozmusuz demektir.
# AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
# BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
# CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
# DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
# EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE
# FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
# GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG
# HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
Write-Output "UZUN_TEST_OK"
$items = Get-ChildItem "C:\Users\lenovo\Desktop" -ErrorAction SilentlyContinue
Write-Output ("DESKTOP_ADET=" + @($items).Count)
foreach ($i in $items) { Write-Output ("ITEM=" + $i.Name) }
$od = Get-ChildItem "C:\Users\lenovo\OneDrive\Desktop" -ErrorAction SilentlyContinue
Write-Output ("ONEDRIVE_ADET=" + @($od).Count)
foreach ($i in $od) { Write-Output ("OD_ITEM=" + $i.Name) }
