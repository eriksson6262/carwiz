# Zimní pneu – přehled vozidel

Excel s auty, která potřebují zimní pneu (buyback po 1.11.), rozdělený na HAVEX / ACJ a krátkodobé (Renteon) / dlouhodobé (pravidelné faktury Vyfakturuj). Obsahuje start (opening card) a barevně auta končící v listopadu (oranžová) a prosinci (žlutá).

## Postup
1. **Renteon CZ** (`rxauto.s3.renteon.com`) a **SK** (`cwslovakia.s6.renteon.com`) – v konzoli přihlášené stránky:
   ```js
   const h=angular.element(document.body).injector().get('$http');
   const r=await h.get('api/car/getSimpleList',{params:{IsActive:true,pageIndex:0,pageSize:1000,sortProperty:'Id',sortDirection:'ASC'}});
   JSON.stringify(r.data.map(c=>({id:c.Id,spz:c.RegistrationPlateNumber,model:c.CarModelName,sipp:c.CarCategorySIPP,
     office:c.OfficeCode,fleet:c.CarFleetName,status:c.Status,act:c.LastCarActivityDefinitionName,bb:c.BuyBackDate,
     rem:c.InternalRemark,vin:c.ChassisNumber,km:c.Mileage,first:c.FirstCarActivityDate})))
   ```
   → `data/cz.json`, `data/sk.json`. Totéž s `IsActive:false` v CZ → `data/cz_inactive.json`.
2. **Vyfakturuj** → Pravidelné faktury (zrušit případný filtr v hledání). Stránkovat `Data_filter.loadPage(p,1)`, z řádků `div.tr` vzít ID (`crud-pravidelne/<id>/`) a datum „Příští“ → `data/vf_next.json`. Detail každé faktury (`/faktury/crud-pravidelne/<id>/`, pole `crud[odberatelSearch]`, `crud[vfpName]`, `crud[-form-::date::vfpDateStart]`, `crud[vfpRepeatType]`, `crud[-form-::date::vfpDateEnd]`, `crud[vfpRepeatCount]`, `crud[items][text][]`) → `data/vf_raw.json`.
3. `python3 zimni_pneu.py [YYYY-MM-DD]` → `output/<datum>_Zimni_pneu_prehled.xlsx`.

## Poznámky
- `vfpRepeatCount` = **zbývající** počet dokladů → poslední faktura = příští + (počet − 1) měsíců. `vfpDateEnd` u typu „podle počtu“ je neplatné.
- Vynechává auta fakturovaná na HAVEX Mobility a FAM (Fábián).
- Peugeot 3008 = celoroční pneu.
- Nová auta bez štítku HVX/ACJ v interní poznámce padají do listu „Jiný vlastník“.
- `data/` a `output/` jsou v `.gitignore` (jména klientů).
