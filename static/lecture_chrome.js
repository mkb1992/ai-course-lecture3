(function () {
          if (window.__lectureChrome === 53) return;
          window.__lectureChrome = 53;
          window.__crumbForward = true;
          window.__rlhfForward = true;

          function clickHidden(key) {
            if (!key) return false;
            var nodes = document.querySelectorAll('[class*="st-key-' + key + '"]');
            for (var i = 0; i < nodes.length; i++) {
              var node = nodes[i];
              var btn = node.tagName === "BUTTON" ? node : node.querySelector("button");
              if (btn) {
                btn.click();
                return true;
              }
            }
            if (key === "rlhf_ctrl_ok" || key.indexOf("llama_ctrl_ok") === 0 || key.indexOf("ctx_ctrl_ok_") === 0) {
              var formKey = key === "rlhf_ctrl_ok"
                ? "rlhf_ctrl_form"
                : key.indexOf("llama_ctrl_ok") === 0
                  ? key.replace("llama_ctrl_ok", "llama_ctrl_form")
                  : key.replace("ctx_ctrl_ok_", "ctx_ctrl_form_");
              var submit = document.querySelector('[class*="st-key-' + formKey + '"] button');
              if (!submit && key.indexOf("ctx_ctrl_ok_") !== 0) {
                submit = document.querySelector('[data-testid="stFormSubmitButton"] button');
              }
              if (submit) {
                submit.click();
                return true;
              }
            }
            return false;
          }

          function activePick(menu, kind) {
            var active = menu.querySelector('[data-rlhf-pick="' + kind + '"].is-active');
            if (active) return active.getAttribute("data-rlhf-value");
            var current = menu.querySelector('[data-rlhf-row="' + kind + '"] .rlhf-control-current');
            if (current) {
              var text = (current.textContent || "").trim();
              if (text) return text;
            }
            return "Auto";
          }

          function collectRlhfDraft(menu) {
            var draft = {
              output_length: activePick(menu, "tok"),
              reasoning: activePick(menu, "rsn"),
              verbosity: activePick(menu, "vrb"),
              temperature: null
            };
            var tempEnabled = menu.querySelector("[data-temp-enabled]");
            var tempVisible = !tempEnabled || tempEnabled.style.display !== "none";
            var manual = menu.querySelector('[data-rlhf-temp-mode="Manual"].is-active');
            var tempCurrent = menu.querySelector('[data-rlhf-row="tmp"] .rlhf-control-current');
            var tempLabel = tempCurrent ? (tempCurrent.textContent || "").trim() : "";
            if (tempVisible && manual) {
              var rangeEl = menu.querySelector("[data-rlhf-temp-range]");
              draft.temperature = rangeEl ? parseFloat(rangeEl.value) : 0.7;
            } else if (tempLabel && tempLabel !== "Auto" && tempLabel !== "Not supported") {
              var parsed = parseFloat(tempLabel);
              if (!isNaN(parsed)) draft.temperature = parsed;
            }
            return draft;
          }

          function writeDraft(key, draft) {
            var input = document.querySelector(
              '[class*="st-key-' + key + '"] textarea, ' +
              '[class*="st-key-' + key + '"] input'
            );
            if (!input) return false;
            var proto = input.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
            var setter = Object.getOwnPropertyDescriptor(proto, "value").set;
            setter.call(input, JSON.stringify(draft));
            input.dispatchEvent(new Event("input", { bubbles: true }));
            input.dispatchEvent(new Event("change", { bubbles: true }));
            return true;
          }

          function writeRlhfDraft(draft) {
            return writeDraft("rlhf_controls_draft", draft);
          }

          function rangeDraft(menu, kind) {
            var fly = menu.querySelector('[data-rlhf-row="' + kind + '"]');
            if (!fly) return null;
            var manual = fly.querySelector('[data-range-choice="Manual"].is-active');
            var current = fly.querySelector(".rlhf-control-current");
            var label = current ? (current.textContent || "").trim() : "";
            if (manual) {
              var rangeEl = fly.querySelector("[data-range-input]");
              return rangeEl ? parseFloat(rangeEl.value) : null;
            }
            if (label && label !== "Auto") {
              var parsed = parseFloat(label);
              if (!isNaN(parsed)) return parsed;
            }
            return null;
          }

          function collectLlamaDraft(menu) {
            return {
              output_length: activePick(menu, "tok"),
              temperature: rangeDraft(menu, "tmp"),
              top_p: rangeDraft(menu, "topp"),
              frequency_penalty: rangeDraft(menu, "freq")
            };
          }

          function formatRange(value, digits) {
            var text = parseFloat(value).toFixed(digits);
            if (text.indexOf(".") >= 0) text = text.replace(/0+$/, "").replace(/[.]$/, "");
            return text || "0";
          }

          function llamaScope() {
            var el = document.querySelector("[data-llama-scope]");
            return el ? (el.getAttribute("data-llama-scope") || "") : "";
          }

          function writeLlamaDraft(draft) {
            var scope = llamaScope();
            return writeDraft(scope ? "llama_" + scope + "_controls_draft" : "llama_controls_draft", draft);
          }

          var allow = { ArrowDown: 1, ArrowUp: 1, Enter: 1, Escape: 1, Tab: 1, Home: 1, End: 1 };

          function lockInput(el) {
            el.setAttribute("readonly", "readonly");
            el.setAttribute("inputmode", "none");
            el.setAttribute("autocomplete", "off");
            el.style.caretColor = "transparent";
            if (el.dataset.dropdownLocked === "1") return;
            el.dataset.dropdownLocked = "1";
            function block(e) {
              if (e.type === "keydown" && allow[e.key]) return;
              e.preventDefault();
              e.stopImmediatePropagation();
            }
            ["keydown", "keypress", "beforeinput", "paste", "cut", "drop"].forEach(function (type) {
              el.addEventListener(type, block, true);
            });
          }

          function wireOpenOnClick(select) {
            if (select.dataset.fullClick === "1") return;
            select.dataset.fullClick = "1";
            select.addEventListener("click", function (e) {
              if (select.querySelector("input:disabled")) return;
              if (select.getAttribute("aria-disabled") === "true") return;
              if (e.target.closest("svg")) return;
              var svgs = select.querySelectorAll("svg");
              var chevron = null;
              svgs.forEach(function (svg) {
                var path = svg.querySelector("path");
                var d = path ? path.getAttribute("d") || "" : "";
                if (d.indexOf("M12 2C6.47") === -1) chevron = svg;
              });
              if (!chevron && svgs.length) chevron = svgs[svgs.length - 1];
              if (!chevron) return;
              var host = chevron.closest("button") || chevron.parentElement;
              ["mousedown", "mouseup", "click"].forEach(function (type) {
                host.dispatchEvent(new window.MouseEvent(type, { bubbles: true, cancelable: true, view: window }));
              });
            });
          }

          function fitChatInput(el) {
            if (el.dataset.fitting === "1") return;
            el.dataset.fitting = "1";
            el.style.setProperty("padding", "0px", "important");
            el.style.setProperty("color", "#111111", "important");
            el.style.setProperty("-webkit-text-fill-color", "#111111", "important");
            el.style.setProperty("caret-color", "#111111", "important");
            el.style.setProperty("height", "auto", "important");
            var next = el.value ? Math.min(Math.max(el.scrollHeight, 22), 88) : 22;
            el.style.setProperty("height", next + "px", "important");
            el.style.setProperty("overflow-y", next >= 88 ? "auto" : "hidden", "important");
            if (next < 88) el.scrollTop = 0;
            requestAnimationFrame(function () {
              el.dataset.fitting = "0";
            });
          }

          function wireChatInput(el) {
            if (el.dataset.chatFit === "1") return;
            el.dataset.chatFit = "1";
            ["input", "keyup", "keydown", "change", "paste"].forEach(function (type) {
              el.addEventListener(type, function () {
                fitChatInput(el);
                requestAnimationFrame(function () { fitChatInput(el); });
              });
            });
            fitChatInput(el);
          }

          function pinThread(el) {
            if (!el.dataset.chatScrollWired) {
              el.dataset.chatScrollWired = "1";
              el.dataset.stickBottom = "1";
              el.addEventListener("scroll", function () {
                var gap = el.scrollHeight - el.scrollTop - el.clientHeight;
                el.dataset.stickBottom = gap < 80 ? "1" : "0";
              }, { passive: true });
            }
            if (el.dataset.stickBottom !== "0") {
              el.scrollTop = el.scrollHeight;
            }
          }

          var fileHint = "Accepts Word, PDF or text only";
          var fileReject = "Only Word, PDF or text files are accepted.";

          function hintFileUi() {
            document.querySelectorAll('[data-testid="stChatInputFileUploadButton"]').forEach(function (btn) {
              btn.setAttribute("aria-label", fileHint);
            });
            document.querySelectorAll('[data-testid="stTooltipContent"]').forEach(function (el) {
              var text = el.textContent || "";
              if (/Upload or drag|drag and drop|Accepts Word, PDF or text only/i.test(text)) {
                el.textContent = fileHint;
                if (el.parentElement) el.parentElement.style.display = "none";
              }
            });
            document.querySelectorAll('[data-testid="stTooltipErrorContent"]').forEach(function (el) {
              var text = el.textContent || "";
              if (/not allowed/i.test(text)) el.textContent = fileReject;
            });
            document.querySelectorAll('[data-testid="stFileChip"] [role="alert"]').forEach(function (el) {
              var text = el.textContent || "";
              if (/not allowed/i.test(text)) el.textContent = "Error: " + fileReject;
            });
          }

          function wireTempRange() {
            document.querySelectorAll("[data-rlhf-temp-range]").forEach(function (el) {
              if (el.dataset.tempWired === "1") return;
              el.dataset.tempWired = "1";
              el.addEventListener("input", function () {
                var value = parseFloat(el.value).toFixed(1);
                var readout = el.parentElement && el.parentElement.querySelector(".rlhf-temp-readout");
                if (readout) readout.textContent = value;
                var fly = el.closest(".rlhf-control-flyout");
                var label = fly && fly.querySelector(".rlhf-control-current");
                if (label) label.textContent = value;
              });
            });
            document.querySelectorAll("[data-range-input]").forEach(function (el) {
              if (el.dataset.rangeWired === "1") return;
              el.dataset.rangeWired = "1";
              el.addEventListener("input", function () {
                var digits = parseInt(el.getAttribute("data-range-digits") || "1", 10);
                var value = formatRange(el.value, digits);
                var readout = el.parentElement && el.parentElement.querySelector(".rlhf-temp-readout");
                if (readout) readout.textContent = value;
                var fly = el.closest(".rlhf-control-flyout");
                var label = fly && fly.querySelector(".rlhf-control-current");
                if (label) label.textContent = value;
              });
            });
          }

          function wireStopOverlay() {
            document.querySelectorAll(".model-chat-shell").forEach(function (shell) {
              var generating = shell.getAttribute("data-generating") === "1";
              var host = ctxHost(shell);
              if (host) host.classList.toggle("is-generating", generating);
              var btnHost = host && host.querySelector(
                '[data-testid="stChatInput"] div:has(> [data-testid="stChatInputSubmitButton"])'
              );
              if (!btnHost) return;
              var overlay = btnHost.querySelector("[data-chat-stop]");
              if (generating) {
                if (!overlay) {
                  overlay = document.createElement("button");
                  overlay.type = "button";
                  overlay.setAttribute("data-chat-stop", "1");
                  overlay.setAttribute("aria-label", "Stop generating");
                  overlay.className = "chat-stop-overlay";
                  btnHost.appendChild(overlay);
                }
                var slot = shell.getAttribute("data-ctx-slot") || "";
                if (slot) overlay.setAttribute("data-ctx-stop", slot);
                else overlay.removeAttribute("data-ctx-stop");
              } else if (overlay) {
                overlay.remove();
              }
            });
            var lesson = document.querySelector(".st-key-lesson_block");
            if (lesson && !document.querySelector("[class*='st-key-ctx_pane_']")) {
              lesson.classList.toggle(
                "is-generating",
                !!document.querySelector(".model-chat-shell[data-generating='1']")
              );
            }
          }

          function ctxHost(shell) {
            return (shell && shell.closest('[class*="st-key-ctx_pane_"]')) ||
              document.querySelector(".st-key-lesson_block");
          }

          function ctxComposerArea(host) {
            if (!host) return null;
            return host.querySelector(
              '[data-testid="stChatInputTextArea"], [data-testid="stChatInput"] textarea'
            );
          }

          function fillCtxComposer() {
            var shells = document.querySelectorAll(".model-chat-shell[data-ctx-prompt]");
            var block = document.querySelector(".st-key-lesson_block");
            if (block) block.classList.toggle("is-ctx", shells.length > 0);
            window.__ctxFillStamp = window.__ctxFillStamp || {};
            shells.forEach(function (shell) {
              var host = ctxHost(shell);
              var area = ctxComposerArea(host);
              if (!area) return;
              var prompt = shell.getAttribute("data-ctx-prompt") || "";
              var armed = shell.getAttribute("data-ctx-armed") === "1";
              var stamp = shell.getAttribute("data-ctx-stamp") || "0";
              var slot = shell.getAttribute("data-ctx-slot") || "";
              var setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value").set;
              var applied = window.__ctxFillStamp[slot];
              if (!armed) {
                window.__ctxFillStamp[slot] = stamp;
                return;
              }
              if (area.disabled || !prompt) return;
              if (applied === stamp) return;
              setter.call(area, prompt);
              area.dispatchEvent(new Event("input", { bubbles: true }));
              area.dispatchEvent(new Event("change", { bubbles: true }));
              area.dataset.ctxPrompt = prompt;
              window.__ctxFillStamp[slot] = stamp;
              fitChatInput(area);
            });
          }

          function lockedCtx(area) {
            var host = area && area.closest && area.closest('[class*="st-key-ctx_pane_"]');
            if (!host) return null;
            var shell = host.querySelector(".model-chat-shell[data-ctx-prompt]");
            if (!shell || shell.getAttribute("data-ctx-armed") !== "1") return null;
            if (shell.getAttribute("data-ctx-thread") === "1") return null;
            return { host: host, shell: shell };
          }

          function restoreCtxPrompt(area, shell) {
            var prompt = shell.getAttribute("data-ctx-prompt") || "";
            if (area.value === prompt) return;
            var setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value").set;
            setter.call(area, prompt);
          }

          function showCtxFirstCard(host, place) {
            if (!host) return;
            var card = host.querySelector("[data-ctx-first-card]");
            if (!card) {
              card = document.createElement("div");
              card.className = "ctx-first-card";
              card.setAttribute("data-ctx-first-card", "1");
              card.setAttribute("role", "status");
              card.innerHTML =
                '<span class="ctx-first-card-mark" aria-hidden="true"></span>' +
                "<span>This is the first turn. You need to send the prompt as it is.</span>";
              host.appendChild(card);
            }
            card.classList.toggle("is-clear", place === "clear");
            card.classList.add("is-on");
            clearTimeout(card._hide);
            card._hide = setTimeout(function () {
              if (card._hold) return;
              card.classList.remove("is-on");
            }, 3200);
          }

          function ctxFirstHost(clearBtn) {
            var shell = clearBtn && clearBtn.closest && clearBtn.closest(".model-chat-shell");
            if (!shell || shell.getAttribute("data-ctx-thread") === "1") return null;
            return shell.closest('[class*="st-key-ctx_pane_"]') || shell.parentElement;
          }

          function blockCtxEdit(e) {
            var area = e.target && e.target.closest && e.target.closest(
              '[data-testid="stChatInput"] textarea, [data-testid="stChatInputTextArea"]'
            );
            if (!area) return;
            var lock = lockedCtx(area);
            if (!lock) return;
            var typing = e.type === "beforeinput" || e.type === "paste" || e.type === "cut" || e.type === "drop";
            var keyWipe = e.type === "keydown" && (
              e.key === "Backspace" || e.key === "Delete" ||
              ((e.metaKey || e.ctrlKey) && (e.key === "x" || e.key === "X")) ||
              (e.key.length === 1 && !e.metaKey && !e.ctrlKey && !e.altKey)
            );
            if (!typing && !keyWipe) return;
            e.preventDefault();
            e.stopPropagation();
            restoreCtxPrompt(area, lock.shell);
            showCtxFirstCard(lock.host, "input");
          }

          function wireCtxFileChip() {
            document.querySelectorAll(".model-chat-shell").forEach(function (shell) {
              var host = ctxHost(shell);
              if (!host) return;
              var box = host.querySelector(
                '[data-testid="stChatInput"] div:has(> [data-testid="stChatInputTextArea"])'
              );
              if (!box) return;
              var name = shell.getAttribute("data-ctx-file") || "";
              var chip = box.querySelector("[data-ctx-file-chip]");
              if (!name) {
                if (chip) chip.remove();
                box.classList.remove("has-ctx-file");
                return;
              }
              if (!chip) {
                chip = document.createElement("div");
                chip.setAttribute("data-ctx-file-chip", "1");
                chip.className = "ctx-file-chip";
                chip.innerHTML =
                  '<span class="ctx-file-chip-icon" aria-hidden="true"></span>' +
                  '<span class="ctx-file-chip-name"></span>';
                box.insertBefore(chip, box.firstChild);
              }
              var label = chip.querySelector(".ctx-file-chip-name");
              if (label && label.textContent !== name) label.textContent = name;
              box.classList.add("has-ctx-file");
            });
          }

          function wireUploadChips() {
            document.querySelectorAll('.st-key-lesson_block [data-testid="stChatInput"]').forEach(function (input) {
              if (input.closest('[class*="st-key-ctx_pane_"]')) return;
              var chips = input.querySelector('[data-testid="stFileChips"]');
              var hasFile = !!(chips && chips.querySelector('[data-testid="stFileChip"]'));
              input.classList.toggle("has-upload", hasFile);
              if (!chips) return;
              chips.querySelectorAll('[data-testid="stFileChipName"]').forEach(function (name) {
                var full = name.getAttribute("title") || "";
                if (full && name.textContent !== full) name.textContent = full;
              });
            });
          }

          function centerCanvasToolbar() {
            document.querySelectorAll('.st-key-nn_draw iframe').forEach(function (frame) {
              function center() {
                try {
                  var doc = frame.contentDocument;
                  if (!doc) return;
                  var send = doc.querySelector('img[title="Send to Streamlit"]');
                  var toolbar = send && send.parentElement;
                  if (!toolbar) return;
                  toolbar.style.setProperty("left", "50%", "important");
                  toolbar.style.setProperty("transform", "translateX(-50%)", "important");
                  toolbar.style.setProperty("justify-content", "center", "important");
                } catch (_error) {
                  // The component can briefly be unavailable while Streamlit replaces it.
                }
              }
              if (frame.dataset.nnToolbarWired !== "1") {
                frame.dataset.nnToolbarWired = "1";
                frame.addEventListener("load", function () {
                  center();
                  setTimeout(center, 120);
                  setTimeout(center, 400);
                });
              }
              center();
              setTimeout(center, 120);
            });
          }

          function scan() {
            document.querySelectorAll('[data-testid="stSelectbox"] input, [data-baseweb="select"] input').forEach(lockInput);
            document.querySelectorAll('[data-baseweb="select"]').forEach(wireOpenOnClick);
            document.querySelectorAll('[data-testid="stChatInput"] textarea, [data-testid="stChatInputTextArea"]').forEach(wireChatInput);
            document.querySelectorAll(".model-chat-thread").forEach(pinThread);
            hintFileUi();
            wireTempRange();
            wireStopOverlay();
            fillCtxComposer();
            wireCtxFileChip();
            wireUploadChips();
            centerCanvasToolbar();
          }

          document.addEventListener("mouseover", function (e) {
            var clearBtn = e.target.closest && e.target.closest("[data-ctx-clear]");
            if (!clearBtn || (e.relatedTarget && clearBtn.contains(e.relatedTarget))) return;
            var host = ctxFirstHost(clearBtn);
            if (!host) return;
            showCtxFirstCard(host, "clear");
            var card = host.querySelector("[data-ctx-first-card]");
            if (card) card._hold = true;
          });

          document.addEventListener("mouseout", function (e) {
            var clearBtn = e.target.closest && e.target.closest("[data-ctx-clear]");
            if (!clearBtn || (e.relatedTarget && clearBtn.contains(e.relatedTarget))) return;
            var host = ctxFirstHost(clearBtn);
            if (!host) return;
            var card = host.querySelector("[data-ctx-first-card]");
            if (!card) return;
            card._hold = false;
            clearTimeout(card._hide);
            card._hide = setTimeout(function () { card.classList.remove("is-on"); }, 160);
          });

          document.addEventListener("click", function (e) {
            var stopBtn = e.target.closest("[data-chat-stop]");
            if (stopBtn) {
              e.preventDefault();
              e.stopPropagation();
              var ctxStop = stopBtn.getAttribute("data-ctx-stop");
              clickHidden(ctxStop ? "ctx_stop_" + ctxStop : "chat_stop");
              return;
            }
            var crumb = e.target.closest(".crumb-link");
            if (crumb) {
              e.preventDefault();
              clickHidden("crumb_" + (crumb.getAttribute("data-level") || "lecture"));
              return;
            }
            if (e.target.closest(".rlhf-bar.is-locked") && !e.target.closest(".ctx-doc-dd")) {
              e.preventDefault();
              return;
            }
            var companyOpt = e.target.closest("[data-rlhf-company]");
            if (companyOpt) {
              e.preventDefault();
              clickHidden("rlhf_co_" + companyOpt.getAttribute("data-rlhf-company"));
              return;
            }
            var llamaModeOpt = e.target.closest("[data-llama-mode]");
            if (llamaModeOpt) {
              e.preventDefault();
              clickHidden("llama_mode_" + llamaScope() + "_" + llamaModeOpt.getAttribute("data-llama-mode"));
              return;
            }
            function ctxPickId(label) {
              return String(label || "").replace(/\./g, "_");
            }
            var ctxTok = e.target.closest("[data-ctx-tok]");
            if (ctxTok) {
              e.preventDefault();
              var tokBar = ctxTok.closest("[data-ctx-slot]");
              var tokSlot = tokBar ? (tokBar.getAttribute("data-ctx-slot") || "") : "";
              clickHidden("ctx_tok_" + tokSlot + "_" + ctxPickId(ctxTok.getAttribute("data-ctx-tok")));
              return;
            }
            var ctxTemp = e.target.closest("[data-ctx-temp]");
            if (ctxTemp) {
              e.preventDefault();
              var tempBar = ctxTemp.closest("[data-ctx-slot]");
              var tempSlot = tempBar ? (tempBar.getAttribute("data-ctx-slot") || "") : "";
              clickHidden("ctx_temp_" + tempSlot + "_" + ctxPickId(ctxTemp.getAttribute("data-ctx-temp")));
              return;
            }
            var ctxModeOpt = e.target.closest("[data-ctx-mode]");
            if (ctxModeOpt) {
              e.preventDefault();
              var ctxHost = ctxModeOpt.closest("[data-ctx-slot]");
              var ctxSlot = ctxHost ? (ctxHost.getAttribute("data-ctx-slot") || "") : "";
              clickHidden("ctx_mode_" + ctxSlot + "_" + ctxModeOpt.getAttribute("data-ctx-mode"));
              return;
            }
            var modeOpt = e.target.closest("[data-rlhf-mode]");
            if (modeOpt) {
              e.preventDefault();
              clickHidden("rlhf_mode_" + modeOpt.getAttribute("data-rlhf-mode"));
              return;
            }
            var modelOpt = e.target.closest("[data-rlhf-model]");
            if (modelOpt) {
              e.preventDefault();
              clickHidden("rlhf_md_" + modelOpt.getAttribute("data-rlhf-model"));
              return;
            }
            var pickOpt = e.target.closest("[data-rlhf-pick]");
            if (pickOpt) {
              e.preventDefault();
              var menu = pickOpt.closest(".rlhf-dd-menu");
              var kind = pickOpt.getAttribute("data-rlhf-pick") || "";
              var value = pickOpt.getAttribute("data-rlhf-value") || "";
              if (menu) {
                menu.querySelectorAll('[data-rlhf-pick="' + kind + '"]').forEach(function (item) {
                  item.classList.toggle("is-active", item.getAttribute("data-rlhf-value") === value);
                });
                var current = menu.querySelector('[data-rlhf-row="' + kind + '"] .rlhf-control-current');
                if (current) current.textContent = value;
                var block = menu.querySelector("[data-temp-policy='reasoning_none']");
                if (block && kind === "rsn") {
                  var on = value === "None";
                  var enabled = block.querySelector("[data-temp-enabled]");
                  var locked = block.querySelector("[data-temp-locked]");
                  if (enabled) enabled.style.display = on ? "block" : "none";
                  if (locked) locked.style.display = on ? "none" : "block";
                }
              }
              return;
            }
            var rangeMode = e.target.closest("[data-range-choice]");
            if (rangeMode) {
              e.preventDefault();
              var rangeCard = rangeMode.closest(".rlhf-length-card");
              var choice = rangeMode.getAttribute("data-range-choice") || "Auto";
              if (rangeCard) {
                rangeCard.querySelectorAll("[data-range-choice]").forEach(function (item) {
                  item.classList.toggle("is-active", item === rangeMode);
                });
                var slider = rangeCard.querySelector(".rlhf-temp-slider");
                if (slider) slider.classList.toggle("is-hidden", choice !== "Manual");
                var rowCur = rangeMode.closest(".rlhf-control-flyout");
                var label = rowCur && rowCur.querySelector(".rlhf-control-current");
                if (label) {
                  if (choice === "Auto") label.textContent = "Auto";
                  else {
                    var range = rangeCard.querySelector("[data-range-input]");
                    var digits = range ? parseInt(range.getAttribute("data-range-digits") || "1", 10) : 1;
                    label.textContent = range ? formatRange(range.value, digits) : "0";
                  }
                }
              }
              return;
            }
            var tempMode = e.target.closest("[data-rlhf-temp-mode]");
            if (tempMode) {
              e.preventDefault();
              var tempCard = tempMode.closest(".rlhf-length-card");
              var mode = tempMode.getAttribute("data-rlhf-temp-mode") || "Auto";
              if (tempCard) {
                tempCard.querySelectorAll("[data-rlhf-temp-mode]").forEach(function (item) {
                  item.classList.toggle("is-active", item === tempMode);
                });
                var slider = tempCard.querySelector(".rlhf-temp-slider");
                if (slider) slider.classList.toggle("is-hidden", mode !== "Manual");
                var rowCur = tempMode.closest(".rlhf-control-flyout");
                var label = rowCur && rowCur.querySelector(".rlhf-control-current");
                if (label) {
                  if (mode === "Auto") label.textContent = "Auto";
                  else {
                    var range = tempCard.querySelector("[data-rlhf-temp-range]");
                    label.textContent = range ? parseFloat(range.value).toFixed(1) : "0.7";
                  }
                }
              }
              return;
            }
            var ctxOkCtrl = e.target.closest("[data-ctx-ctrl-ok]");
            if (ctxOkCtrl) {
              e.preventDefault();
              var ctxOkMenu = ctxOkCtrl.closest(".rlhf-dd-menu");
              var ctxOkBar = ctxOkCtrl.closest("[data-ctx-slot]");
              var ctxOkSlot = ctxOkBar ? (ctxOkBar.getAttribute("data-ctx-slot") || "") : "";
              if (ctxOkMenu && ctxOkSlot) {
                writeDraft("ctx_controls_draft_" + ctxOkSlot, {
                  output_length: activePick(ctxOkMenu, "tok"),
                  temperature: activePick(ctxOkMenu, "tmp")
                });
                var ctxOkKey = "ctx_ctrl_ok_" + ctxOkSlot;
                setTimeout(function () { clickHidden(ctxOkKey); }, 80);
                setTimeout(function () { clickHidden(ctxOkKey); }, 220);
              }
              return;
            }
            var llamaOkCtrl = e.target.closest("[data-llama-ctrl-ok]");
            if (llamaOkCtrl) {
              e.preventDefault();
              var llamaOkMenu = llamaOkCtrl.closest(".rlhf-dd-menu");
              if (llamaOkMenu) {
                writeLlamaDraft(collectLlamaDraft(llamaOkMenu));
                var llamaOkKey = "llama_ctrl_ok_" + llamaScope();
                setTimeout(function () {
                  clickHidden(llamaOkKey);
                }, 80);
                setTimeout(function () {
                  clickHidden(llamaOkKey);
                }, 220);
              }
              return;
            }
            var okCtrl = e.target.closest("[data-rlhf-ctrl-ok]");
            if (okCtrl) {
              e.preventDefault();
              var okMenu = okCtrl.closest(".rlhf-dd-menu");
              if (okMenu) {
                writeRlhfDraft(collectRlhfDraft(okMenu));
                setTimeout(function () {
                  clickHidden("rlhf_ctrl_ok");
                }, 80);
                setTimeout(function () {
                  clickHidden("rlhf_ctrl_ok");
                }, 220);
              }
              return;
            }
            var flyToggle = e.target.closest("summary.rlhf-control-row");
            if (flyToggle) {
              var fly = flyToggle.closest(".rlhf-control-flyout");
              document.querySelectorAll(".rlhf-control-flyout").forEach(function (el) {
                if (el !== fly) el.removeAttribute("open");
              });
              return;
            }
            var clearChat = e.target.closest("[data-rlhf-clear], [data-llama-clear], [data-ctx-clear]");
            if (clearChat) {
              e.preventDefault();
              var ctxBar = clearChat.closest("[data-ctx-slot]");
              var ctxSlot = ctxBar ? (ctxBar.getAttribute("data-ctx-slot") || "") : "";
              if (clearChat.hasAttribute("data-ctx-clear")) {
                var ctxShell = clearChat.closest(".model-chat-shell");
                if (ctxShell && ctxShell.getAttribute("data-ctx-thread") !== "1") {
                  showCtxFirstCard(ctxShell.closest('[class*="st-key-ctx_pane_"]') || ctxShell.parentElement, "clear");
                  return;
                }
                clickHidden("ctx_clear_" + ctxSlot);
              } else {
                clickHidden(clearChat.hasAttribute("data-llama-clear") ? "llama_clear_" + llamaScope() : "rlhf_clear");
              }
              return;
            }
            var topToggle = e.target.closest("summary.rlhf-dd-toggle");
            if (topToggle) {
              var host = topToggle.closest(".rlhf-dd");
              document.querySelectorAll(".rlhf-dd").forEach(function (el) {
                if (el !== host) el.removeAttribute("open");
              });
              return;
            }
            if (!e.target.closest(".rlhf-dd")) {
              document.querySelectorAll(".rlhf-dd, .rlhf-control-flyout").forEach(function (el) {
                el.removeAttribute("open");
              });
            }
          }, true);

          ["input", "keyup", "paste"].forEach(function (type) {
            document.addEventListener(type, function (e) {
              var el = e.target && e.target.closest && e.target.closest(
                '[data-testid="stChatInput"] textarea, [data-testid="stChatInputTextArea"]'
              );
              if (el) {
                var lock = lockedCtx(el);
                if (lock) restoreCtxPrompt(el, lock.shell);
                fitChatInput(el);
                requestAnimationFrame(function () { fitChatInput(el); });
              }
            }, true);
          });

          ["beforeinput", "keydown", "paste", "cut", "drop"].forEach(function (type) {
            document.addEventListener(type, blockCtxEdit, true);
          });

          scan();
          new MutationObserver(scan).observe(document.body, { childList: true, subtree: true });
        })();
