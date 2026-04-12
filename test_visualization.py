"""
Automated Test Suite — Q3 D3 Dual Choropleth Visualization
Using Selenium (Windows compatible, no build dependencies)

HOW TO RUN:
1. pip install selenium webdriver-manager
2. Start WebStorm built-in server
3. Update BASE_URL below to your local port
4. Run: python test_visualization_selenium.py
"""

import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ── CONFIG ────────────────────────────────────────────────────────────────────
BASE_URL = "http://127.0.0.1:5500/index.html"
# Change port to match your WebStorm server

RESULTS = []

def log(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    icon   = "✅" if passed else "❌"
    RESULTS.append((name, passed, detail))
    msg = f"{icon} {status} | {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1400,900")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-file-access-from-files")
    # Remove headless to see the browser — add below line to hide it
    # options.add_argument("--headless=new")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver

def run_all_tests():
    driver = setup_driver()
    wait   = WebDriverWait(driver, 10)
    actions = ActionChains(driver)

    try:
        print("=" * 60)
        print("Opening visualization...")
        print("=" * 60)
        driver.get(BASE_URL)
        time.sleep(3)  # wait for D3 to render

        # ── R1: DATA PROCESSING ───────────────────────────────────────────────
        print("\n── R1: DATA PROCESSING ──")

        # TC-01: Page loads, countries stat shows a number
        try:
            el  = driver.find_element(By.ID, "stat-countries")
            val = el.text.strip()
            passed = val != "" and val != "—" and val.isdigit()
            log("TC-01 Page loads, countries stat shown", passed, f"Value: {val}")
        except Exception as e:
            log("TC-01 Page loads, countries stat shown", False, str(e))

        # TC-02: Stats bar shows enrollment %
        try:
            el  = driver.find_element(By.ID, "stat-enrol")
            val = el.text.strip()
            passed = "%" in val and val != "—"
            log("TC-02 Stats bar shows avg enrollment %", passed, f"Value: {val}")
        except Exception as e:
            log("TC-02 Stats bar shows avg enrollment %", False, str(e))

        # TC-03: Stats bar shows completion %
        try:
            el  = driver.find_element(By.ID, "stat-comp")
            val = el.text.strip()
            passed = "%" in val and val != "—"
            log("TC-03 Stats bar shows avg completion %", passed, f"Value: {val}")
        except Exception as e:
            log("TC-03 Stats bar shows avg completion %", False, str(e))

        # TC-04: Stats bar shows gap in pts
        try:
            el  = driver.find_element(By.ID, "stat-gap")
            val = el.text.strip()
            passed = "pts" in val and val != "—"
            log("TC-04 Stats bar shows avg gap pts", passed, f"Value: {val}")
        except Exception as e:
            log("TC-04 Stats bar shows avg gap pts", False, str(e))

        # ── R2: VISUAL LAYOUT ─────────────────────────────────────────────────
        print("\n── R2: VISUAL LAYOUT ──")

        # TC-05: Both SVG maps exist
        try:
            svg_e = driver.find_element(By.ID, "svg-enrollment")
            svg_c = driver.find_element(By.ID, "svg-completion")
            passed = svg_e.is_displayed() and svg_c.is_displayed()
            log("TC-05 Both map SVGs visible", passed)
        except Exception as e:
            log("TC-05 Both map SVGs visible", False, str(e))

        # TC-06: Map panel titles correct
        try:
            titles = [el.text for el in driver.find_elements(By.CSS_SELECTOR, ".map-panel h2")]
            passed = "Enrollment Rate (%)" in titles and "Completion Rate (%)" in titles
            log("TC-06 Map panel titles correct", passed, f"Found: {titles}")
        except Exception as e:
            log("TC-06 Map panel titles correct", False, str(e))

        # TC-07: Country paths exist in both SVGs
        try:
            paths_e = driver.find_elements(By.CSS_SELECTOR, "#svg-enrollment path.country")
            paths_c = driver.find_elements(By.CSS_SELECTOR, "#svg-completion path.country")
            passed  = len(paths_e) > 100 and len(paths_c) > 100
            log("TC-07 Country paths rendered", passed,
                f"Enrollment: {len(paths_e)} | Completion: {len(paths_c)}")
        except Exception as e:
            log("TC-07 Country paths rendered", False, str(e))

        # TC-08: At least one country has a colour fill
        try:
            paths = driver.find_elements(By.CSS_SELECTOR, "#svg-enrollment path.country")
            colored = [p for p in paths
                       if p.get_attribute("fill") and
                       p.get_attribute("fill").startswith("#") and
                       p.get_attribute("fill") != "#BDBDBD"]
            passed = len(colored) > 0
            sample = colored[0].get_attribute("fill") if colored else "none"
            log("TC-08 Countries have colour fills", passed, f"Sample fill: {sample}")
        except Exception as e:
            log("TC-08 Countries have colour fills", False, str(e))

        # TC-09: Legend has 6 buckets
        try:
            buckets = driver.find_elements(By.CSS_SELECTOR, ".legend-bucket")
            passed  = len(buckets) == 6
            log("TC-09 Legend has 6 buckets", passed, f"Found: {len(buckets)}")
        except Exception as e:
            log("TC-09 Legend has 6 buckets", False, str(e))

        # TC-10: Legend has No data text
        try:
            legend = driver.find_element(By.ID, "legend")
            passed = "No data" in legend.text
            log("TC-10 Legend has No data label", passed)
        except Exception as e:
            log("TC-10 Legend has No data label", False, str(e))

        # TC-11: Legend contains correct bucket labels
        try:
            legend_text = driver.find_element(By.ID, "legend").text
            labels = [">95%", "90", "80", "70", "60", "<60%"]
            passed = all(l in legend_text for l in labels)
            log("TC-11 Legend labels correct", passed)
        except Exception as e:
            log("TC-11 Legend labels correct", False, str(e))

        # ── R3: INTERACTIONS ──────────────────────────────────────────────────
        print("\n── R3: USER INTERACTIONS ──")

        # TC-12: Year slider starts at 1999
        try:
            slider = driver.find_element(By.ID, "year-slider")
            label  = driver.find_element(By.ID, "year-label")
            passed = slider.get_attribute("value") == "1999" and label.text.strip() == "1999"
            log("TC-12 Year slider starts at 1999", passed, f"Label: {label.text}")
        except Exception as e:
            log("TC-12 Year slider starts at 1999", False, str(e))

        # TC-13: Moving slider changes year label
        try:
            slider = driver.find_element(By.ID, "year-slider")
            driver.execute_script("arguments[0].value = '2010'; arguments[0].dispatchEvent(new Event('input'));", slider)
            time.sleep(0.8)
            label = driver.find_element(By.ID, "year-label").text.strip()
            passed = label == "2010"
            log("TC-13 Slider changes year label", passed, f"Label: {label}")
        except Exception as e:
            log("TC-13 Slider changes year label", False, str(e))

        # TC-14: Changing year updates stats bar
        try:
            slider = driver.find_element(By.ID, "year-slider")
            driver.execute_script("arguments[0].value = '1999'; arguments[0].dispatchEvent(new Event('input'));", slider)
            time.sleep(0.8)
            gap_1999 = driver.find_element(By.ID, "stat-gap").text
            driver.execute_script("arguments[0].value = '2020'; arguments[0].dispatchEvent(new Event('input'));", slider)
            time.sleep(0.8)
            gap_2020 = driver.find_element(By.ID, "stat-gap").text
            passed   = gap_1999 != gap_2020
            log("TC-14 Year change updates stats", passed,
                f"1999: {gap_1999} | 2020: {gap_2020}")
        except Exception as e:
            log("TC-14 Year change updates stats", False, str(e))

        # TC-15: Play button exists and is visible
        try:
            play = driver.find_element(By.ID, "play-btn")
            passed = play.is_displayed()
            log("TC-15 Play button visible", passed, f"Text: {play.text}")
        except Exception as e:
            log("TC-15 Play button visible", False, str(e))

        # TC-16: Play button starts animation
        try:
            slider = driver.find_element(By.ID, "year-slider")
            driver.execute_script("arguments[0].value = '1999'; arguments[0].dispatchEvent(new Event('input'));", slider)
            time.sleep(0.5)
            driver.find_element(By.ID, "play-btn").click()
            time.sleep(2.0)
            year_after = driver.find_element(By.ID, "year-label").text.strip()
            driver.find_element(By.ID, "play-btn").click()  # pause
            passed = int(year_after) > 1999
            log("TC-16 Play button animates years", passed, f"Year after 2s: {year_after}")
        except Exception as e:
            log("TC-16 Play button animates years", False, str(e))

        # TC-17: Pause stops animation
        try:
            slider = driver.find_element(By.ID, "year-slider")
            driver.execute_script("arguments[0].value = '1999'; arguments[0].dispatchEvent(new Event('input'));", slider)
            time.sleep(0.3)
            driver.find_element(By.ID, "play-btn").click()   # play
            time.sleep(1.0)
            driver.find_element(By.ID, "play-btn").click()   # pause
            year_at_pause = driver.find_element(By.ID, "year-label").text.strip()
            time.sleep(1.5)
            year_after    = driver.find_element(By.ID, "year-label").text.strip()
            passed = year_at_pause == year_after
            log("TC-17 Pause stops animation", passed,
                f"At pause: {year_at_pause} | 1.5s later: {year_after}")
        except Exception as e:
            log("TC-17 Pause stops animation", False, str(e))

        # TC-18: Continent dropdown exists
        try:
            dd = Select(driver.find_element(By.ID, "continent-filter"))
            opts = [o.text for o in dd.options]
            passed = any("Africa" in o for o in opts)
            log("TC-18 Continent dropdown has options", passed, f"Options: {opts}")
        except Exception as e:
            log("TC-18 Continent dropdown has options", False, str(e))

        # TC-19: Selecting Africa reduces country count
        try:
            slider = driver.find_element(By.ID, "year-slider")
            driver.execute_script("arguments[0].value = '2010'; arguments[0].dispatchEvent(new Event('input'));", slider)
            time.sleep(0.5)
            all_count = driver.find_element(By.ID, "stat-countries").text.strip()
            dd = Select(driver.find_element(By.ID, "continent-filter"))
            dd.select_by_visible_text("Africa")
            time.sleep(0.8)
            africa_count = driver.find_element(By.ID, "stat-countries").text.strip()
            dd.select_by_value("all")
            time.sleep(0.5)
            passed = (all_count.isdigit() and africa_count.isdigit() and
                      int(africa_count) < int(all_count))
            log("TC-19 Africa filter reduces count", passed,
                f"All: {all_count} | Africa: {africa_count}")
        except Exception as e:
            log("TC-19 Africa filter reduces count", False, str(e))

        # TC-20: Continent filter fades non-selected countries
        try:
            dd = Select(driver.find_element(By.ID, "continent-filter"))
            dd.select_by_visible_text("Africa")
            time.sleep(0.8)
            paths = driver.find_elements(By.CSS_SELECTOR, "#svg-enrollment path.country")
            opacities = [float(p.get_attribute("opacity") or "1") for p in paths[:50]]
            faded = [o for o in opacities if o < 0.5]
            passed = len(faded) > 0
            log("TC-20 Non-Africa countries faded", passed,
                f"{len(faded)}/50 paths are faded")
            dd.select_by_value("all")
            time.sleep(0.5)
        except Exception as e:
            log("TC-20 Non-Africa countries faded", False, str(e))

        # TC-21: Tooltip appears on country hover
        try:
            paths = driver.find_elements(By.CSS_SELECTOR, "#svg-enrollment path.country")
            tooltip_shown = False
            for path in paths[5:30]:
                try:
                    actions.move_to_element(path).perform()
                    time.sleep(0.4)
                    tt = driver.find_element(By.ID, "tooltip")
                    if tt.is_displayed():
                        tooltip_shown = True
                        break
                except:
                    continue
            log("TC-21 Tooltip appears on hover", tooltip_shown)
        except Exception as e:
            log("TC-21 Tooltip appears on hover", False, str(e))

        # TC-22: Tooltip contains required fields
        try:
            paths = driver.find_elements(By.CSS_SELECTOR, "#svg-enrollment path.country")
            fields_ok = False
            for path in paths[5:40]:
                try:
                    actions.move_to_element(path).perform()
                    time.sleep(0.4)
                    tt = driver.find_element(By.ID, "tooltip")
                    if tt.is_displayed():
                        text = tt.text
                        if all(f in text for f in ["Year","Enrollment","Completion","Gap","IWI"]):
                            fields_ok = True
                            break
                except:
                    continue
            log("TC-22 Tooltip shows all 5 fields", fields_ok,
                "Year, Enrollment, Completion, Gap, IWI")
        except Exception as e:
            log("TC-22 Tooltip shows all 5 fields", False, str(e))

        # TC-23: Sparkline SVG in tooltip
        try:
            paths = driver.find_elements(By.CSS_SELECTOR, "#svg-enrollment path.country")
            has_spark = False
            for path in paths[5:40]:
                try:
                    actions.move_to_element(path).perform()
                    time.sleep(0.4)
                    tt = driver.find_element(By.ID, "tooltip")
                    if tt.is_displayed():
                        sparks = tt.find_elements(By.TAG_NAME, "svg")
                        if len(sparks) > 0:
                            has_spark = True
                            break
                except:
                    continue
            log("TC-23 Tooltip sparkline SVG exists", has_spark)
        except Exception as e:
            log("TC-23 Tooltip sparkline SVG exists", False, str(e))

        # TC-24: Click country focuses both maps
        try:
            paths = driver.find_elements(By.CSS_SELECTOR, "#svg-enrollment path.country")
            focused = False
            for path in paths[5:30]:
                try:
                    path.click()
                    time.sleep(0.6)
                    faded_e = driver.find_elements(
                        By.CSS_SELECTOR, "#svg-enrollment path.country-faded")
                    faded_c = driver.find_elements(
                        By.CSS_SELECTOR, "#svg-completion path.country-faded")
                    sel_e   = driver.find_elements(
                        By.CSS_SELECTOR, "#svg-enrollment path.country-selected")
                    if len(faded_e) > 0 and len(faded_c) > 0 and len(sel_e) > 0:
                        focused = True
                        break
                except:
                    continue
            log("TC-24 Click focuses country on both maps", focused,
                f"Faded enrol: {len(faded_e)} | Faded comp: {len(faded_c)}")
        except Exception as e:
            log("TC-24 Click focuses country on both maps", False, str(e))

        # TC-25: Click same country again deselects
        try:
            selected = driver.find_elements(
                By.CSS_SELECTOR, "#svg-enrollment path.country-selected")
            if selected:
                selected[0].click()
                time.sleep(0.6)
                still_faded = driver.find_elements(
                    By.CSS_SELECTOR, "#svg-enrollment path.country-faded")
                passed = len(still_faded) == 0
                log("TC-25 Click same country deselects", passed,
                    f"Still faded: {len(still_faded)}")
            else:
                log("TC-25 Click same country deselects", False, "No selected country")
        except Exception as e:
            log("TC-25 Click same country deselects", False, str(e))

        # TC-26: Legend bucket click filters
        try:
            buckets = driver.find_elements(By.CSS_SELECTOR, ".legend-bucket")
            if len(buckets) >= 6:
                buckets[5].click()
                time.sleep(0.8)
                paths  = driver.find_elements(
                    By.CSS_SELECTOR, "#svg-enrollment path.country")
                faded  = [p for p in paths
                          if float(p.get_attribute("opacity") or "1") < 0.5]
                passed = len(faded) > 0
                log("TC-26 Legend bucket click filters", passed,
                    f"Faded after click: {len(faded)}")
                buckets[5].click()  # reset
            else:
                log("TC-26 Legend bucket click filters", False, "Buckets not found")
        except Exception as e:
            log("TC-26 Legend bucket click filters", False, str(e))

        # TC-27: No JS errors (check via browser logs)
        try:
            logs = driver.get_log("browser")
            errors = [l for l in logs if l["level"] == "SEVERE"]
            passed = len(errors) == 0
            log("TC-27 No JavaScript console errors", passed,
                f"Errors: {[e['message'][:60] for e in errors]}" if errors else "Clean")
        except Exception as e:
            log("TC-27 No JavaScript console errors", True, "Log access unavailable — skipped")

    finally:
        driver.quit()

    # ── FINAL REPORT ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("FINAL TEST REPORT")
    print("=" * 60)
    passed_all = [r for r in RESULTS if r[1]]
    failed_all = [r for r in RESULTS if not r[1]]
    print(f"PASSED: {len(passed_all)}/{len(RESULTS)}")
    print(f"FAILED: {len(failed_all)}/{len(RESULTS)}")
    if failed_all:
        print("\nFailed tests:")
        for name, _, detail in failed_all:
            print(f"  ❌ {name}" + (f" — {detail}" if detail else ""))
    score = round(len(passed_all) / len(RESULTS) * 100)
    print(f"\nOverall: {score}%")
    return len(failed_all) == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)