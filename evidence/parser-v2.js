function f8411(arg0) {
  let paramsEcoPlug;
  let fromResult = arg0;
  if (fromResult) {
    const _Buffer = closure_3_0(closure_3_1[17]).Buffer;
    fromResult = _Buffer.from(arg0);
  }
  const items = [];
  let num2 = 0;
  const items1 = ["WifiSSIDPart1", "WifiSSIDPart2"];
  const items2 = ["WifiPasswordPart1", "WifiPasswordPart2", "WifiPasswordPart3", "WifiPasswordPart4"];
  if (closure_1_0._hasEcoPlugParams(closure_0, closure_1.deviceType)) {
    paramsEcoPlug = closure_0.paramsEcoPlug;
  } else {
    const tmp7 = closure_0;
    paramsEcoPlug = closure_1_0._has3PhaseParams(closure_0, closure_1.deviceType) ? tmp7.params3Phase : tmp7.params;
  }
  const iter = paramsEcoPlug[Symbol.iterator]();
  const nextResult = iter.next();
  if (iter === undefined) {
    return items;
  } else {
    const _default = closure_3_7.default;
    const cloneResult = _default.clone(nextResult);
    try {
      const _Buffer2 = closure_3_0(closure_3_1[17]).Buffer;
      cloneResult.rawData = _Buffer2.alloc(nextResult.length);
      fromResult.copy(cloneResult.rawData, 0, num2, num2 + nextResult.length);
    } catch (tmp20) {
      let num4;
      const _console = console;
      console.log("_getParseFunction rawData.copy: ", tmp20, nextResult);
      if (cloneResult.getComputedFields) {
        cloneResult.computedFields = cloneResult.getComputedFields(closure_1);
        if (cloneResult.computedFields) {
          if (cloneResult.computedFields.factor) {
            cloneResult.factor = cloneResult.computedFields.factor;
            cloneResult.rightSideDigits = cloneResult.computedFields.rightSideDigits;
          }
        }
        if (cloneResult.computedFields) {
          if (cloneResult.computedFields.parseValue) {
            nextResult.parseValue = cloneResult.computedFields.parseValue;
          }
        }
      }
      if (nextResult.parseValueFromRawData) {
        if (nextResult.factor) {
          const _console2 = console;
          console.log("+++++++++++++++++++++++++++ ignoring string and factor members of model when parseValueFromRawData is present", nextResult);
        }
        num4 = arr4.parseValueFromRawData(cloneResult.rawData);
      } else if (nextResult.string) {
        num4 = closure_3_11.readRawDataString(num2, arr4.length, obj);
      } else if (!nextResult.byteArray) {
        if (nextResult.key !== "setPoint") {
          if (nextResult.key !== "measuredFloor") {
            num4 = closure_3_11.readRawDataUint(num2, arr4.length, obj);
          }
        }
        num4 = closure_3_11.readRawDataInt(num2, arr4.length, obj);
      } else {
        num4 = closure_3_11.readRawDataStringPart(num2, arr4.length, obj);
      }
      if (cloneResult.factor) {
        const result = num4 * cloneResult.factor;
        const _Number = Number;
        const toFixed = result.toFixed;
        if (cloneResult.rightSideDigits) {
          num4 = _Number(toFixed(cloneResult.rightSideDigits));
        } else {
          num4 = _Number(toFixed(2));
        }
      }
      if (nextResult.key === "measuredFloor") {
        if (num4 < -60) {
          num4 = 0;
        }
      }
      const field = closure_0.field;
      if (nextResult.parseValue) {
        cloneResult[field] = nextResult.parseValue(num4);
      } else {
        cloneResult[field] = num4;
      }
      items.push(cloneResult);
      num2 = num2 + arr4.length;
    }
  }
}

// ========================================
// Expansion summary: 1 functions decompiled
// Root: F8411, Max depth: 5
// ========================================
