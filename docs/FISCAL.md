# Fiskalizatsiya: ma'lumotlarni tayyorlash (1-bosqich)

**Holat:** faqat ma'lumotlar modeli va hisob. Hech narsa soliq operatoriga
YUBORILMAYDI (`fiscal_mode = "off"`). Provayder (virtual kassa / fiskal
modul / integrator) tanlangach, 2-bosqich (yuborish navbati) quriladi.

## Nima qo'shildi (baza sxemasi v2)

| Jadval | Maydonlar |
|---|---|
| `products` | `ikpu_code`, `package_code`, `vat_rate` (bo'sh = do'konning standart stavkasi) |
| `sale_items` | `ikpu_code`, `package_code`, `vat_rate`, `vat_amount` — sotuv paytidagi "surat" |
| `sales` | `vat_total`, `fiscal_status`, `fiscal_receipt_id`, `fiscal_sign`, `fiscal_qr_url`, `fiscal_at`, `fiscal_error`, `fiscal_attempts` |
| `refunds` | yuqoridagi `sales` bilan bir xil fiskal maydonlar + `vat_total` |
| `refund_items` | `vat_amount` |
| sozlamalar | `store_tin` (STIR), `store_legal_name`, `default_vat_rate`, `fiscal_mode` |

Fiskal holat: `none` (fiskallashtirilmagan) → `pending` (navbatda) →
`sent` / `failed`. Eski cheklar `none` bo'lib qoladi.

## Qoidalar
- QQS **qator bo'yicha** hisoblanadi va tiyingacha yaxlitlanadi
  (ROUND_HALF_UP); chek jami = qatorlar yig'indisi.
- Mahsulot stavkasi **aniq 0** bo'lsa — QQSsiz; **bo'sh (None)** bo'lsa —
  do'konning standart stavkasi. Bu ikkisi farq qiladi.
- Chekdagi IKPU/qadoq/stavka sotuv paytida **qotiriladi**: mahsulot
  keyin o'zgarsa ham chek o'zgarmaydi; **qaytarish** QQS'ni chekdagi
  (asl) stavka bo'yicha hisoblaydi.
- Qaytarish faqat asl chek fiskallashtirilgan bo'lsa fiskal qaytarish
  chekini (`pending`) talab qiladi.

## TASDIQLASH KERAK (taxminlar)
1. **Narxlar QQSni o'z ichiga oladi** (qqs = summa × stavka / (100 + stavka)).
   Agar narxlar QQSsiz bo'lsa, formula va chek jami o'zgaradi.
2. **IKPU/qadoq kodi uzunligi** ataylab tekshirilmaydi (faqat raqamlar,
   ≤ 20 belgi): soliq talabi o'zgarishi mumkin. Haqiqiy format provayder
   hujjatidan.
3. **QQS stavkasi**: kod hech qanday stavkani "tabiiy" deb olmaydi —
   standart 0, do'kon egasi Sozlamalarda kiritadi. Joriy stavka va
   do'kon QQS to'lovchisimi — buxgalter bilan tekshiring.
4. Qaysi **soliq rejimi** va fiskalizatsiya majburiymi — buxgalter/soliq.

## Keyingi qadamlar
2. Chek chop etish (termoprinter, ESC/POS) — fiskal rekvizitlarsiz ham foydali.
3. "Fiskal provayder" abstraksiyasi: navbat, qayta urinish, takroriy
   yuborishdan himoya, holat ko'rsatish; tanlangan operator uchun bitta
   amalga oshirish (uning hujjati va test muhiti bo'yicha).
4. Operator test konturida sinov, keyin jangovar.

## Eslatma: versiya
Sxema v2 bazasini eski dastur (≤ 1.2.0) OCHMAYDI (DatabaseTooNewError,
ma'lumotga tegilmaydi) — foydalanuvchi avval dasturni yangilashi kerak.
Shuning uchun bu o'zgarish yangi reliz bilan birga chiqadi.
