function f8442(arg0) {
  closure_0 = arg0;
  const timerId = setTimeout(function() { /* body not rendered: F8443 */ }, 25000);
  const _default = closure_3_7.default;
  const cloneResult = _default.clone(closure_0);
  console.log("Modified settings: ", cloneResult);
  const obj1 = {};
  const items = [];
  if (closure_1_0.settingsService) {
    const characteristics = closure_1_0.bleSpec.services.settings.characteristics;
    const characteristics2 = closure_1_0.bleSpec.services.info.characteristics;
    const _console = console;
    console.log("******************************************** modifiedSettings: ******************************************** IN");
    const iter = cloneResult[Symbol.iterator]();
    const nextResult = iter.next();
    if (iter === undefined) {
      const _console6 = console;
      console.log("******************************************** modifiedSettings: ******************************************** OUT");
      const iter3 = characteristics[Symbol.iterator]();
      const nextResult1 = iter3.next();
      while (iter3 !== undefined) {
        let tmp77 = nextResult1;
        if (nextResult1.field !== "value") {
          continue;
        } else {
          let tmp331 = nextResult1;
          if (!tmp77.params) {
            let tmp78 = closure_1_0;
            let tmp79 = nextResult1;
            let tmp80 = closure_1;
            if (!closure_1_0._hasEcoPlugParams(tmp77, closure_1)) {
              let tmp81 = closure_1_0;
              let tmp82 = nextResult1;
              let tmp83 = closure_1;
            }
          }
          let tmp84 = nextResult1;
          if (tmp77.name !== "productButtons") {
            let tmp85 = nextResult1;
            if (tmp77.name !== "productButtons2") {
              let tmp86 = nextResult1;
              if (tmp77.name !== "productParamC") {
                let tmp87 = items;
                let tmp89 = closure_1_0;
                let currentPeripheral = closure_1_0.currentPeripheral;
                let id;
                let push = items.push;
                let tmp88 = closure_3_11;
                let writeCharacteristicAsync = closure_3_11.writeCharacteristicAsync;
                if (currentPeripheral != null) {
                  let tmp92 = currentPeripheral;
                  id = tmp90.id;
                }
                let tmp93 = nextResult1;
                let arr1 = push(writeCharacteristicAsync(id, tmp77.data, tmp77.handle));
              }
            }
          }
          continue;
        }
        continue;
      }
      try {
        const iter4 = characteristics2[Symbol.iterator]();
        const nextResult2 = iter4.next();
        if (iter4 === undefined) {
          if (closure_1 === closure_3_21) {
            if (closure_2 >= closure_3_22) {
              try {
                const iter7 = characteristics2[Symbol.iterator]();
                const nextResult3 = iter7.next();
                if (iter7 !== undefined) {
                  if (nextResult3.name === "productStateB") {
                    let data7;
                    if (nextResult3.data) {
                      const _Buffer5 = closure_3_0(closure_3_1[17]).Buffer;
                      data7 = _Buffer5.from(tmp168.data);
                    } else {
                      data7 = tmp168.data;
                    }
                    nextResult3.data = data7;
                    if (nextResult3.params) {
                      const iter8 = cloneResult[Symbol.iterator]();
                      const nextResult4 = iter8.next();
                      if (iter8 !== undefined) {
                        let num8 = 0;
                        let key2 = nextResult4.originalKey;
                        if (!key2) {
                          key2 = iter9.key;
                        }
                        const params3 = tmp174.params;
                        const iter10 = params3[Symbol.iterator]();
                        const nextResult5 = iter10.next();
                        const tmp180 = key2;
                        if (iter10 !== undefined) {
                          if (nextResult5.key === tmp180) {
                            const _console21 = console;
                            console.log("wattageCharacteristic modified ", nextResult4);
                            try {
                              if (nextResult5.length === 1) {
                                const data9 = tmp168.data;
                                data9.writeUInt8(nextResult4.value, num8);
                              } else if (nextResult5.length === 2) {
                                const data8 = tmp168.data;
                                data8.writeUInt16LE(nextResult4.value, num8);
                              }
                            } catch (tmp196) {
                              const _console11 = console;
                              console.error("saveSettings 4 ", tmp196);
                            }
                          }
                          num8 = num8 + arr6.length;
                        }
                      }
                    }
                    const currentPeripheral3 = closure_1_0.currentPeripheral;
                    let id1;
                    const push3 = items.push;
                    const writeCharacteristicAsync3 = closure_3_11.writeCharacteristicAsync;
                    if (currentPeripheral3 != null) {
                      id1 = tmp203.id;
                    }
                    push3(writeCharacteristicAsync3(id1, nextResult3.data, nextResult3.handle));
                  }
                }
              } catch (tmp208) {
                const _console12 = console;
                console.error("saveSettings 5 ", tmp208);
              }
            }
          }
          if (closure_1 === closure_3_6.default.ECO_PLUG) {
            let flag2 = false;
            let flag3 = false;
            const iter13 = cloneResult[Symbol.iterator]();
            const nextResult6 = iter13.next();
            if (iter13 === undefined) {
              const iter12 = characteristics[Symbol.iterator]();
              const nextResult7 = iter12.next();
              while (iter12 !== undefined) {
                let data12;
                let tmp294 = nextResult7;
                if (nextResult7.data) {
                  let tmp296 = closure_3_0;
                  let tmp297 = closure_3_1;
                  let _Buffer12 = closure_3_0(closure_3_1[17]).Buffer;
                  let tmp298 = nextResult7;
                  data12 = _Buffer12.from(tmp294.data);
                } else {
                  let tmp295 = nextResult7;
                  data12 = tmp294.data;
                }
                nextResult7.data = data12;
                let tmp299 = nextResult7;
                if (tmp294.name === "productButtons2") {
                  let tmp375 = flag2;
                  if (tmp375) {
                    let tmp300 = flag3;
                    if (tmp300) {
                      if (tmp294.paramsEcoPlug) {
                        let tmp302 = nextResult7;
                        let paramsEcoPlug6 = tmp301.paramsEcoPlug;
                        let tmp303 = paramsEcoPlug6;
                        for (const item10769 of paramsEcoPlug6) {
                          if (item10769.key === "WifiPasswordPart4") {
                            let tmp306 = obj2;
                            let tmp307 = nextResult7;
                            let tmp308 = obj2;
                            let num12 = 0;
                            let num13 = 60;
                            let num14 = 64;
                            let copyResult = obj2.copy(tmp294.data, 0, 60, 64);
                            let _console19 = console;
                            let logResult4 = console.log("Modified settings wifiPassword - part 4: ", tmp294.data, tmp294.handle);
                          } else {
                            let tmp305 = item10769;
                            if (tmp304.key === "WifiSSIDPart2") {
                              let tmp376 = obj;
                              let tmp377 = nextResult7;
                              let tmp378 = obj;
                              let num30 = 4;
                              let num31 = 16;
                              let num32 = 32;
                              let copyResult1 = obj.copy(tmp294.data, 4, 16, 32);
                              let _console22 = console;
                              let logResult5 = console.log("Modified settings wifiSSID - part 2: ", tmp294.data, tmp294.handle);
                            }
                          }
                          continue;
                        }
                        let _console20 = console;
                        let tmp311 = nextResult7;
                        let logResult6 = console.log("Modified settings productButtons2 ", tmp294.data, tmp294.handle);
                        let tmp313 = items;
                        let tmp315 = closure_1_0;
                        let currentPeripheral5 = closure_1_0.currentPeripheral;
                        let id2;
                        let push5 = items.push;
                        let tmp314 = closure_3_11;
                        let writeCharacteristicAsync5 = closure_3_11.writeCharacteristicAsync;
                        if (currentPeripheral5 != null) {
                          let tmp318 = currentPeripheral5;
                          id2 = tmp316.id;
                        }
                        let tmp319 = nextResult7;
                        let push5Result = push5(writeCharacteristicAsync5(id2, tmp294.data, tmp294.handle));
                      }
                    }
                  }
                }
                continue;
              }
            } else if (nextResult6.key === "wifiSSID") {
              if (nextResult6.key === "wifiSSID") {
                const value1 = iter11.value;
                const _Buffer8 = closure_3_0(closure_3_1[17]).Buffer;
                const allocResult = _Buffer8.alloc(32);
                allocResult.fill("\0");
                const set2 = allocResult.set;
                const _Buffer9 = closure_3_0(closure_3_1[17]).Buffer;
                set2(_Buffer9.from(value1));
                const _console14 = console;
                console.log("Modified settings wifiSSID buffer ", allocResult);
              } else {
                const value = iter11.value;
                const _Buffer6 = closure_3_0(closure_3_1[17]).Buffer;
                const allocResult1 = _Buffer6.alloc(64);
                allocResult1.fill("\0");
                const set = allocResult1.set;
                const _Buffer7 = closure_3_0(closure_3_1[17]).Buffer;
                const result = set(_Buffer7.from(value));
                const _console13 = console;
                console.log("Modified settings wifiPassword buffer ", allocResult1);
              }
              try {
                if (nextResult6.key === "wifiSSID") {
                  for (const item10576 of characteristics2) {
                    let tmp229 = item10576;
                    if (item10576.name === "productCounterC") {
                      let data10;
                      let tmp346 = item10576;
                      if (tmp229.data) {
                        let tmp231 = closure_3_0;
                        let tmp232 = closure_3_1;
                        let _Buffer10 = closure_3_0(closure_3_1[17]).Buffer;
                        let tmp233 = item10576;
                        data10 = _Buffer10.from(tmp229.data);
                      } else {
                        let tmp230 = item10576;
                        data10 = tmp229.data;
                      }
                      tmp229.data = data10;
                      if (tmp229.paramsEcoPlug) {
                        let tmp235 = item10576;
                        let paramsEcoPlug = tmp234.paramsEcoPlug;
                        let tmp236 = paramsEcoPlug;
                        for (const item10597 of paramsEcoPlug) {
                          if (item10597.key === "WifiSSIDPart1") {
                            let tmp237 = obj;
                            let tmp238 = item10576;
                            let tmp239 = obj;
                            let num9 = 0;
                            let num10 = 0;
                            let num11 = 16;
                            let copyResult2 = obj.copy(tmp229.data, 0, 0, 16);
                            let tmp241 = items;
                            let tmp243 = closure_1_0;
                            let currentPeripheral4 = closure_1_0.currentPeripheral;
                            let id3;
                            let push4 = items.push;
                            let tmp242 = closure_3_11;
                            let writeCharacteristicAsync4 = closure_3_11.writeCharacteristicAsync;
                            if (currentPeripheral4 != null) {
                              let tmp246 = currentPeripheral4;
                              id3 = tmp244.id;
                            }
                            let tmp247 = item10576;
                            let push4Result = push4(writeCharacteristicAsync4(id3, tmp229.data, tmp229.handle));
                          }
                          continue;
                        }
                      }
                    }
                    continue;
                  }
                }
                for (const item10629 of characteristics) {
                  let data11;
                  let tmp251 = item10629;
                  if (item10629.data) {
                    let tmp253 = closure_3_0;
                    let tmp254 = closure_3_1;
                    let _Buffer11 = closure_3_0(closure_3_1[17]).Buffer;
                    let tmp255 = item10629;
                    data11 = _Buffer11.from(tmp251.data);
                  } else {
                    let tmp252 = item10629;
                    data11 = tmp251.data;
                  }
                  item10629.data = data11;
                  let tmp256 = nextResult6;
                  if (iter11.key === "wifiPassword") {
                    let tmp347 = item10629;
                    if (tmp251.name === "productParamC") {
                      if (tmp251.paramsEcoPlug) {
                        let tmp273 = item10629;
                        let paramsEcoPlug4 = tmp272.paramsEcoPlug;
                        let tmp274 = paramsEcoPlug4;
                        for (const item10695 of paramsEcoPlug4) {
                          if (item10695.key === "WifiPasswordPart1") {
                            let tmp367 = obj2;
                            let tmp368 = item10629;
                            let tmp369 = obj2;
                            let num27 = 0;
                            let num28 = 0;
                            let num29 = 20;
                            let copyResult3 = obj2.copy(tmp251.data, 0, 0, 20);
                            let tmp371 = items;
                            let tmp373 = closure_1_0;
                            let currentPeripheral8 = closure_1_0.currentPeripheral;
                            let id4;
                            let push8 = items.push;
                            let tmp372 = closure_3_11;
                            let writeCharacteristicAsync8 = closure_3_11.writeCharacteristicAsync;
                            if (currentPeripheral8 != null) {
                              let tmp275 = currentPeripheral8;
                              id4 = tmp374.id;
                            }
                            let tmp277 = item10629;
                            let push8Result = push8(writeCharacteristicAsync8(id4, tmp251.data, tmp251.handle));
                            let _console17 = console;
                            let logResult9 = console.log("Modified settings wifiPassword - part 1: ", tmp251.data, tmp251.handle);
                          }
                          continue;
                        }
                      }
                    } else {
                      let tmp348 = item10629;
                      if (tmp251.name === "nonce") {
                        if (tmp251.paramsEcoPlug) {
                          let tmp265 = item10629;
                          let paramsEcoPlug3 = tmp264.paramsEcoPlug;
                          let tmp266 = paramsEcoPlug3;
                          for (const item10672 of paramsEcoPlug3) {
                            if (item10672.key === "WifiPasswordPart2") {
                              let tmp359 = obj2;
                              let tmp360 = item10629;
                              let tmp361 = obj2;
                              let num24 = 0;
                              let num25 = 20;
                              let num26 = 40;
                              let copyResult4 = obj2.copy(tmp251.data, 0, 20, 40);
                              let tmp363 = items;
                              let tmp365 = closure_1_0;
                              let currentPeripheral7 = closure_1_0.currentPeripheral;
                              let id5;
                              let push7 = items.push;
                              let tmp364 = closure_3_11;
                              let writeCharacteristicAsync7 = closure_3_11.writeCharacteristicAsync;
                              if (currentPeripheral7 != null) {
                                let tmp267 = currentPeripheral7;
                                id5 = tmp366.id;
                              }
                              let tmp269 = item10629;
                              let push7Result = push7(writeCharacteristicAsync7(id5, tmp251.data, tmp251.handle));
                              let _console16 = console;
                              let logResult10 = console.log("Modified settings wifiPassword - part 2: ", tmp251.data, tmp251.handle);
                            }
                            continue;
                          }
                        }
                      } else {
                        let tmp349 = item10629;
                        if (tmp251.name === "productButtons") {
                          if (tmp251.paramsEcoPlug) {
                            let tmp257 = item10629;
                            let paramsEcoPlug2 = tmp350.paramsEcoPlug;
                            let tmp258 = paramsEcoPlug2;
                            for (const item10649 of paramsEcoPlug2) {
                              if (item10649.key === "WifiPasswordPart3") {
                                let tmp351 = obj2;
                                let tmp352 = item10629;
                                let tmp353 = obj2;
                                let num21 = 0;
                                let num22 = 40;
                                let num23 = 60;
                                let copyResult5 = obj2.copy(tmp251.data, 0, 40, 60);
                                let tmp355 = items;
                                let tmp357 = closure_1_0;
                                let currentPeripheral6 = closure_1_0.currentPeripheral;
                                let id6;
                                let push6 = items.push;
                                let tmp356 = closure_3_11;
                                let writeCharacteristicAsync6 = closure_3_11.writeCharacteristicAsync;
                                if (currentPeripheral6 != null) {
                                  let tmp259 = currentPeripheral6;
                                  id6 = tmp358.id;
                                }
                                let tmp261 = item10629;
                                let push6Result = push6(writeCharacteristicAsync6(id6, tmp251.data, tmp251.handle));
                                let _console15 = console;
                                let logResult11 = console.log("Modified settings wifiPassword - part 3: ", tmp251.data, tmp251.handle);
                              }
                              continue;
                            }
                          }
                        }
                      }
                    }
                  }
                  let tmp280 = item10629;
                  if (tmp251.name === "productButtons2") {
                    if (tmp251.paramsEcoPlug) {
                      let tmp282 = item10629;
                      let paramsEcoPlug5 = tmp281.paramsEcoPlug;
                      let tmp283 = paramsEcoPlug5;
                      for (const item10720 of paramsEcoPlug5) {
                        let tmp284 = item10720;
                        let tmp285 = nextResult6;
                        if (iter11.key === "wifiPassword") {
                          let tmp286 = item10720;
                          if (tmp284.key === "WifiPasswordPart4") {
                            flag3 = true;
                            continue;
                          }
                        }
                        let tmp287 = nextResult6;
                        if (iter11.key === "wifiSSID") {
                          let tmp288 = item10720;
                          if (tmp284.key === "WifiSSIDPart2") {
                            flag2 = true;
                          }
                        }
                      }
                    }
                  }
                  continue;
                }
              } catch (tmp289) {
                const _console18 = console;
                console.log("saveSettings 6 ", tmp289);
              }
            }
          }
          const _clearTimeout2 = clearTimeout;
          clearTimeout(timerId);
          const obj10 = {};
          obj10.ok = true;
          arg0(obj10);
        } else if (nextResult2.name === "productLocation") {
          let data4;
          if (nextResult2.data) {
            const _Buffer2 = closure_3_0(closure_3_1[17]).Buffer;
            data4 = _Buffer2.from(tmp99.data);
          } else {
            data4 = tmp99.data;
          }
          nextResult2.data = data4;
          if (nextResult2.params) {
            const iter5 = cloneResult[Symbol.iterator]();
            const nextResult8 = iter5.next();
            if (iter5 !== undefined) {
              let data5;
              if (nextResult2.data) {
                const _Buffer3 = closure_3_0(closure_3_1[17]).Buffer;
                data5 = _Buffer3.from(tmp99.data);
              } else {
                data5 = tmp99.data;
              }
              nextResult2.data = data5;
              let num7 = 0;
              const params2 = tmp333.params;
              for (const item10323 of params2) {
                let arr3 = item10323;
                let tmp116 = nextResult8;
                if (iter6.key === "productLocation") {
                  let tmp117 = item10323;
                  if (arr3.key === "productLocation") {
                    let tmp138 = closure_3_7;
                    let _default1 = closure_3_7.default;
                    let tmp139 = cloneResult;
                    let value3 = _default1.find(function() { /* body not rendered: F8444 */ }, tmp3).value;
                    let tmp140 = value3;
                    if (value3.length < 15) {
                      let length;
                      do {
                        let tmp141 = tmp140;
                        let text = `${tmp140} `;
                        tmp140 = text;
                        length = `${tmp140} `.length;
                      } while (length < 15);
                    }
                    let tmp143 = closure_3_0;
                    let tmp144 = closure_3_1;
                    let _Buffer4 = closure_3_0(closure_3_1[17]).Buffer;
                    let tmp145 = tmp140;
                    let fromResult = _Buffer4.from(tmp140);
                    let tmp146 = nextResult2;
                    let tmp147 = num7;
                    let copyResult6 = fromResult.copy(tmp99.data, num7);
                    let tmp149 = num7;
                    let tmp150 = item10323;
                    num7 = num7 + arr3.length;
                    continue;
                  }
                }
                let tmp118 = nextResult8;
                let tmp119 = item10323;
                if (iter6.key === arr3.key) {
                  try {
                    let _console7 = console;
                    let tmp120 = item10323;
                    let logResult13 = console.log("-- p2 in", arr3);
                    let tmp122 = item10323;
                    if (arr3.writeValue) {
                      let tmp128 = nextResult8;
                      let writeValueResult = arr3.writeValue(iter6.value);
                      let obj5 = writeValueResult;
                      if (obj5) {
                        let tmp132 = writeValueResult;
                        let tmp133 = nextResult2;
                        let tmp134 = num7;
                        let copyResult7 = obj5.copy(tmp99.data, num7);
                      } else {
                        let _console8 = console;
                        let tmp130 = item10323;
                        let logResult14 = console.log("no param buffer for key: ", arr3.key);
                        continue;
                      }
                      continue;
                    } else if (arr3.length === 1) {
                      let tmp124 = nextResult2;
                      let data6 = tmp99.data;
                      let tmp125 = nextResult8;
                      let tmp126 = num7;
                      let writeUInt8Result1 = data6.writeUInt8(iter6.value, num7);
                    } else {
                      let tmp123 = item10323;
                      if (arr3.length === 2) {
                        let tmp334 = nextResult2;
                        let data14 = tmp99.data;
                        let tmp335 = nextResult8;
                        let tmp336 = num7;
                        let writeUInt16LEResult1 = data14.writeUInt16LE(iter6.value, num7);
                      }
                    }
                  } catch (tmp136) {
                    let _console9 = console;
                    let errorResult2 = console.error("locationString error ", tmp136);
                  }
                }
              }
            }
          }
          const currentPeripheral2 = closure_1_0.currentPeripheral;
          let id7;
          const push2 = items.push;
          const writeCharacteristicAsync2 = closure_3_11.writeCharacteristicAsync;
          if (currentPeripheral2 != null) {
            id7 = tmp154.id;
          }
          push2(writeCharacteristicAsync2(id7, nextResult2.data, closure_1_0.productLocationCharacteristic));
        }
      } catch (tmp160) {
        const _console10 = console;
        console.error("saveSettings 3 ", tmp160);
      }
    } else {
      let key = nextResult.originalKey;
      if (!key) {
        key = iter2.key;
      }
      const tmp16 = key;
      if (nextResult.factor) {
        const _console2 = console;
        console.log("---- factor, value in ", nextResult.factor, nextResult.value);
        const _Math = Math;
        nextResult.value = Math.round(nextResult.value / nextResult.factor);
      }
      const _console3 = console;
      console.log("---- use value ", nextResult.value);
      for (const item10134 of characteristics) {
        let tmp24 = item10134;
        if (item10134.field !== "value") {
          continue;
        } else {
          let tmp324 = item10134;
          if (!tmp24.params) {
            let tmp25 = closure_1_0;
            let tmp26 = item10134;
            let tmp27 = closure_1;
            if (!closure_1_0._hasEcoPlugParams(tmp24, closure_1)) {
              let tmp28 = closure_1_0;
              let tmp29 = item10134;
              let tmp30 = closure_1;
            }
          }
          let tmp31 = item10134;
          if (tmp24.name !== "productButtons") {
            let tmp325 = item10134;
            if (tmp24.name !== "productButtons2") {
              let data;
              let params;
              let tmp326 = item10134;
              if (tmp24.data) {
                let tmp33 = closure_3_0;
                let tmp34 = closure_3_1;
                let _Buffer = closure_3_0(closure_3_1[17]).Buffer;
                let tmp35 = item10134;
                data = _Buffer.from(tmp24.data);
              } else {
                let tmp32 = item10134;
                data = tmp24.data;
              }
              tmp24.data = data;
              let num5 = 0;
              let tmp36 = closure_1_0;
              let tmp37 = item10134;
              let tmp38 = closure_1;
              if (closure_1_0._hasEcoPlugParams(tmp24, closure_1)) {
                let tmp43 = item10134;
                params = tmp24.paramsEcoPlug;
              } else {
                let tmp39 = closure_1_0;
                let tmp40 = item10134;
                let tmp41 = closure_1;
                let tmp42 = item10134;
                if (closure_1_0._has3PhaseParams(tmp24, closure_1)) {
                  params = tmp24.params3Phase;
                } else {
                  params = tmp24.params;
                }
              }
              let tmp44 = params;
              let tmp45 = params;
              for (const item10178 of params) {
                let arr2 = item10178;
                let tmp46 = key;
                if (item10178.key === tmp16) {
                  try {
                    let tmp47 = item10178;
                    let tmp48 = item10178;
                    if (arr2.writeValue) {
                      let tmp59 = nextResult;
                      let writeValueResult1 = arr2.writeValue(iter2.value);
                      let obj4 = writeValueResult1;
                      if (obj4) {
                        let tmp63 = writeValueResult1;
                        let tmp64 = item10134;
                        let tmp65 = num5;
                        let copyResult8 = obj4.copy(tmp24.data, num5);
                      } else {
                        let _console4 = console;
                        let tmp61 = item10178;
                        let logResult17 = console.log("no param buffer for key: ", arr2.key);
                        continue;
                      }
                      continue;
                    } else if (arr2.length === 1) {
                      let tmp55 = item10134;
                      let data3 = tmp24.data;
                      let tmp56 = nextResult;
                      let tmp57 = num5;
                      let writeUInt8Result2 = data3.writeUInt8(iter2.value, num5);
                    } else {
                      let tmp49 = item10178;
                      if (arr2.length === 2) {
                        let tmp51 = item10134;
                        let data2 = tmp24.data;
                        let tmp52 = nextResult;
                        let tmp53 = num5;
                        let writeUInt16LEResult2 = data2.writeUInt16LE(iter2.value, num5);
                      } else {
                        let tmp50 = item10178;
                        if (arr2.length === 4) {
                          let tmp327 = item10134;
                          let data13 = tmp24.data;
                          let tmp328 = nextResult;
                          let tmp329 = num5;
                          let writeUInt32LEResult = data13.writeUInt32LE(iter2.value, num5);
                        }
                      }
                    }
                  } catch (tmp67) {
                    let _console5 = console;
                    let errorResult4 = console.error("saveSettings error 1", tmp67);
                  }
                }
                let tmp69 = num5;
                let tmp70 = item10178;
                num5 = num5 + arr2.length;
                continue;
              }
            }
          }
          continue;
        }
        continue;
      }
    }
  } else {
    obj1.ok = false;
    arg0(obj1);
    const _clearTimeout = clearTimeout;
    clearTimeout(timerId);
  }
}

// ========================================
// Expansion summary: 1 functions decompiled
// Root: F8442, Max depth: 5
// ========================================
