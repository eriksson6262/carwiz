// Import nových vozidel do Renteonu – spustit v konzoli přihlášeného Renteonu (rxauto.s3.renteon.com)
// Použije Angular $http aplikace (přidá autorizaci sám). Žádná hesla v kódu.
(async () => {
  const $h = angular.element(document.body).injector().get('$http');

  // ---- PARAMETRY ----
  const BUYBACK = '21.04.2027.';                 // DD.MM.YYYY.
  const OPEN = { P: [25, '21.10.2026. 18:38'],   // Praha: officeId, datum otevření
                 O: [26, '22.10.2026. 08:00'] }; // Ostrava
  const REMARK = 'ACJ ČGP Zimní pneu';           // InternalRemark
  const SUPPLIER = 349779, OWNER = 349779;       // EURO FLEET SERVIS
  const COLOR = 12;                              // Vícebarevný
  const FLEET = 7, MILEAGE = 30, INV_FROM = 164, INV_PREFIX = '26/';
  const TANK_SECTION = 1;                        // 1/8

  // typ: [ModelId, CategoryId, FuelTypeId, nádrž l, ccm, kW]
  const SPEC = {
    kamiq:   [871, 222, 1, 55, 1498, 110],
    karoqB:  [619, 1168, 1, 55, 1498, 110],
    karoqD:  [619, 1168, 2, 55, 1968, 110],
    octavia: [2075, 214, 1, 55, 1498, 110],
    kodiaq:  [2255, 231, 2, 65, 1968, 110],
    superb:  [623, 218, 1, 66, 1498, 110],
  };
  // [SPZ, VIN, 'P'|'O', typ]
  const CARS = [
    // ['9H00000', 'TMB...', 'P', 'kamiq'],
  ];

  const out = [];
  for (let i = 0; i < CARS.length; i++) {
    const [spz, vin, br, typ] = CARS[i], s = SPEC[typ];
    try {
      const car = (await $h.post('/api/car', JSON.stringify({
        IsActive: true, InventoryCode: INV_PREFIX + (INV_FROM + i), ChassisNumber: vin,
        RegistrationPlateNumber: spz, CarModelId: s[0], CarCategoryId: s[1], FuelTypeId: s[2],
        FuelTankSize: s[3], FuelTankSizeForFullFuelTank: s[3], ElectroTankSize: 0, GasTankSize: 0,
        EngineDisplacement: s[4], EnginePowerKW: s[5], Mileage: MILEAGE, ServiceInterval: 30000,
        CarFleetId: FLEET, CarColorId: COLOR, SupplierId: SUPPLIER, OwnerId: OWNER,
        BuyBackDate: BUYBACK, InternalRemark: REMARK, UsesFuel: true, UsesElectro: false,
        UsesGas: false, AllowUpgrade: false,
      }))).data;
      const [office, dt] = OPEN[br];
      const a = (await $h.get('/api/carActivity/getNewByDate',
        { params: { carId: car.Id, carActivityDefinitionId: 109, dateOut: dt } })).data;
      Object.assign(a, { OfficeOutId: office, OfficeEstimatedInId: office, OfficeInId: office,
        DateOut: dt, DateEstimatedIn: dt, DateIn: dt, MilesOut: MILEAGE, MilesIn: MILEAGE,
        FuelTankSectionIn: TANK_SECTION, FuelTankIn: Math.round(s[3] * TANK_SECTION / 8) });
      const act = (await $h.post('/api/carActivity', JSON.stringify(a))).data;
      out.push([spz, car.Id, car.InventoryCode, act.Number]);
    } catch (e) { out.push([spz, 'ERR', e.status, JSON.stringify(e.data)]); }
  }
  console.table(out);
})();
