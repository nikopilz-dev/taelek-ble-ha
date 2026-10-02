function f8415(arg0) {
  closure_0 = arg0;
  const timerId = setTimeout(function() { /* body not rendered: F8416 */ }, 15000);
  closure_1 = timerId;
  const obj = {};
  closure_2 = obj;
  const items = [];
  closure_3 = [];
  if (closure_1_0.settingsService) {
    if (closure_1_0.BleDiscover) {
      const BleDiscover = closure_1_0.BleDiscover;
      BleDiscover.remove();
      closure_1_0.BleDiscover = undefined;
    }
    const obj1 = {};
    obj1.bootloaderVersion = closure_1_0.bootloader;
    obj1.deviceType = closure_0;
    const characteristics = closure_1_0.bleSpec.services.info.characteristics;
    const iter = characteristics[Symbol.iterator]();
    const nextResult = iter.next();
    while (iter !== undefined) {
      let tmp14 = nextResult;
      if (nextResult.name === "productLocation") {
        let tmp15 = nextResult;
        if (tmp14.params) {
          let tmp53 = closure_3_11;
          let tmp54 = nextResult;
          let tmp55 = closure_1_0;
          let result = closure_3_11.findCharacteristicByUuid(tmp14.uuid, closure_1_0.infoCharacteristics);
          let tmp57 = result;
          if (tmp57) {
            let tmp59 = result;
            let tmp60 = nextResult;
            tmp57._debugName = tmp14.name;
            tmp14.handle = tmp57;
            let tmp61 = closure_1_0;
            let tmp62 = obj1;
            tmp14.parse = closure_1_0._getParseFunction(tmp14, tmp9);
            let tmp63 = items;
            let currentPeripheral3 = closure_1_0.currentPeripheral;
            let id;
            let push3 = items.push;
            let tmp64 = closure_3_11;
            let readCharacteristicAsync3 = closure_3_11.readCharacteristicAsync;
            if (currentPeripheral3 != null) {
              let tmp67 = currentPeripheral3;
              id = tmp65.id;
            }
            let tmp68 = result;
            let tmp69 = nextResult;
            let push3Result = push3(readCharacteristicAsync3(id, tmp57, tmp14));
            continue;
          } else {
            let _console3 = console;
            let logResult = console.log("no characteristic found");
            continue;
          }
          continue;
        }
      }
      let tmp16 = nextResult;
      if (tmp14.name === "productStateB") {
        let tmp17 = closure_0;
        let tmp18 = closure_3_21;
        if (closure_0 === closure_3_21) {
          let tmp19 = closure_1;
          let tmp20 = closure_3_22;
          if (closure_1 >= closure_3_22) {
            let tmp35 = closure_3_11;
            let tmp36 = nextResult;
            let tmp37 = closure_1_0;
            let result1 = closure_3_11.findCharacteristicByUuid(tmp14.uuid, closure_1_0.infoCharacteristics);
            let tmp39 = result1;
            if (tmp39) {
              let tmp41 = result1;
              let tmp42 = nextResult;
              tmp39._debugName = tmp14.name;
              tmp14.handle = tmp39;
              let tmp43 = closure_1_0;
              let tmp44 = obj1;
              tmp14.parse = closure_1_0._getParseFunction(tmp14, tmp9);
              let tmp45 = items;
              let currentPeripheral2 = closure_1_0.currentPeripheral;
              let id1;
              let push2 = items.push;
              let tmp46 = closure_3_11;
              let readCharacteristicAsync2 = closure_3_11.readCharacteristicAsync;
              if (currentPeripheral2 != null) {
                let tmp49 = currentPeripheral2;
                id1 = tmp47.id;
              }
              let tmp50 = result1;
              let tmp51 = nextResult;
              let push2Result = push2(readCharacteristicAsync2(id1, tmp39, tmp14));
            } else {
              let _console2 = console;
              let logResult1 = console.log("no characteristic found");
              continue;
            }
            continue;
          }
        }
      }
      let tmp21 = nextResult;
      if (tmp14.name === "productCounterC") {
        let tmp100 = closure_0;
        let tmp101 = closure_3_6;
        if (closure_0 === closure_3_6.default.ECO_PLUG) {
          let tmp102 = closure_3_11;
          let tmp103 = nextResult;
          let tmp104 = closure_1_0;
          let result2 = closure_3_11.findCharacteristicByUuid(tmp14.uuid, closure_1_0.infoCharacteristics);
          let tmp106 = result2;
          if (tmp106) {
            let tmp23 = result2;
            let tmp24 = nextResult;
            tmp106._debugName = tmp14.name;
            tmp14.handle = tmp106;
            let tmp25 = closure_1_0;
            let tmp26 = obj1;
            tmp14.parse = closure_1_0._getParseFunction(tmp14, tmp9);
            let tmp27 = items;
            let currentPeripheral = closure_1_0.currentPeripheral;
            let id2;
            let push = items.push;
            let tmp28 = closure_3_11;
            let readCharacteristicAsync = closure_3_11.readCharacteristicAsync;
            if (currentPeripheral != null) {
              let tmp31 = currentPeripheral;
              id2 = tmp29.id;
            }
            let tmp32 = result2;
            let tmp33 = nextResult;
            let arr1 = push(readCharacteristicAsync(id2, tmp106, tmp14));
          } else {
            let _console = console;
            let logResult2 = console.log("no characteristic found");
            continue;
          }
          continue;
        }
      }
    }
    const characteristics2 = closure_1_0.bleSpec.services.settings.characteristics;
    for (const item10157 of characteristics2) {
      let tmp73 = item10157;
      if (!item10157.params) {
        let tmp74 = closure_1_0;
        let tmp75 = item10157;
        let tmp76 = obj1;
        if (!closure_1_0._hasEcoPlugParams(tmp73, tmp9.deviceType)) {
          let tmp77 = closure_1_0;
          let tmp78 = item10157;
          let tmp79 = obj1;
        }
        continue;
      }
      let tmp80 = closure_3_11;
      let tmp81 = item10157;
      let tmp82 = closure_1_0;
      let result3 = closure_3_11.findCharacteristicByUuid(tmp73.uuid, closure_1_0.settingsCharacteristics);
      let tmp84 = result3;
      if (tmp84) {
        let tmp86 = result3;
        let tmp87 = item10157;
        tmp84._debugName = tmp73.name;
        tmp73.handle = tmp84;
        let tmp88 = closure_1_0;
        let tmp89 = obj1;
        tmp73.parse = closure_1_0._getParseFunction(tmp73, tmp9);
        let tmp90 = items;
        let currentPeripheral4 = closure_1_0.currentPeripheral;
        let id3;
        let push4 = items.push;
        let tmp91 = closure_3_11;
        let readCharacteristicAsync4 = closure_3_11.readCharacteristicAsync;
        if (currentPeripheral4 != null) {
          let tmp94 = currentPeripheral4;
          id3 = tmp92.id;
        }
        let tmp95 = result3;
        let tmp96 = item10157;
        let push4Result = push4(readCharacteristicAsync4(id3, tmp84, tmp73));
      } else {
        let _console4 = console;
        let logResult3 = console.log("no characteristic found");
        continue;
      }
      continue;
    }
    const _default = closure_3_13.default;
    const allResult = _default.all(items);
    const nextPromise = allResult.then(function() { /* body not rendered: F8417 */ });
    nextPromise.then(function() { /* body not rendered: F8420 */ });
  } else {
    obj.ok = false;
    arg0(obj);
    const _clearTimeout = clearTimeout;
    clearTimeout(timerId);
  }
}

// ========================================
// Expansion summary: 1 functions decompiled
// Root: F8415, Max depth: 4
// ========================================
