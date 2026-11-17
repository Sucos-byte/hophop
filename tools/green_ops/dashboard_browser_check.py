# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Optional Playwright smoke/screenshots; not a dashboard runtime dependency."""
import argparse
import json
from pathlib import Path
import threading
from dashboard import make_server
from dashboard_artifacts import ArtifactStore


def check(output):
    from playwright.sync_api import sync_playwright, expect
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    store=ArtifactStore();server=make_server(0,store)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    errors=[];external=[];checks=[]
    base=f'http://127.0.0.1:{server.server_port}'
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            for width,height,label in ((1440,1000,'desktop'),(390,844,'narrow')):
                page=browser.new_page(viewport={'width':width,'height':height},reduced_motion='reduce')
                page.on('pageerror',lambda error:errors.append(str(error)))
                page.on('console',lambda msg:errors.append(msg.text) if msg.type=='error' else None)
                page.on('request',lambda r:external.append(r.url) if not r.url.startswith(base+'/') else None)
                page.goto(base);page.wait_for_selector('h1')
                assert 'undefined' not in page.locator('.page-head').inner_text()
                for view in ('overview','experiments','predictions','gates','faults'):
                    # Native anchors activated by keyboard, not mouse-only navigation.
                    nav=page.locator('nav a[href="#'+view+'"]');nav.focus();page.keyboard.press('Enter')
                    expect(nav).to_have_attribute('aria-current','page')
                    expect(page.locator('main')).to_have_attribute('aria-busy','false')
                    if view=='experiments':page.wait_for_selector('tbody tr')
                    if view=='predictions':page.wait_for_selector('svg')
                    assert page.locator('main .error').count()==0,(label,view,page.locator('main').inner_text())
                    assert page.locator('.evidence-banner').is_visible()
                    overflow=page.evaluate('document.documentElement.scrollWidth>window.innerWidth')
                    if overflow:
                        page.screenshot(path=str(output/(label+'-'+view+'-overflow.png')),full_page=True)
                        nodes=page.evaluate('() => [...document.querySelectorAll("body *")].filter(e=>e.getBoundingClientRect().right>innerWidth+1).map(e=>({tag:e.tagName,cls:e.className,right:e.getBoundingClientRect().right,width:e.getBoundingClientRect().width})).slice(0,30)')
                        raise AssertionError((label,view,'page overflow',nodes))
                    checks.append(f'{label}/{view}: rendered; keyboard navigation; persistent provenance; no page overflow')
                    if view=='overview':page.screenshot(path=str(output/(label+'-overview.png')),full_page=False)
                    if view=='experiments':
                        first=page.locator('tbody tr').first.inner_text();page.get_by_role('button',name='Next',exact=True).click()
                        expect(page.locator('tbody tr').first).not_to_have_text(first)
                        assert page.locator('tbody tr').count()==20
                    if view=='predictions':
                        page.get_by_label('Study',exact=True).select_option('week8')
                        page.wait_for_selector('text=Observed row coverage')
                        page.wait_for_selector('svg')
                        assert 'family coverage' in page.locator('main').inner_text()
                        page.get_by_label('Panel',exact=True).select_option('airtime-high')
                        page.wait_for_selector('svg');assert page.locator('main .error').count()==0
                        page.screenshot(path=str(output/(label+'-intervals.png')),full_page=True)
                    if view=='gates':
                        page.get_by_label('Saved status',exact=True).select_option('PASS')
                        regression=page.locator('.gate-card').filter(has_text='same features regression')
                        assert '0 mW / 0%' in regression.inner_text()
                        assert '148.06 mW' in regression.inner_text()
                        page.get_by_label('Saved status',exact=True).select_option('FAIL')
                        battery=page.locator('.gate-card').filter(has_text='battery five years fail')
                        assert 'engineering range' in battery.inner_text() and 'mAh' in battery.inner_text()
                        assert 'Missing / undefined years' not in battery.inner_text()
                        page.get_by_label('Saved status',exact=True).select_option('PASS')
                        assert page.locator('.gate-card').count()>=1
                        assert 'EXPLICIT UNVALIDATED RESEARCH OVERRIDE' in page.locator('main').inner_text()
                        page.get_by_label('Saved status',exact=True).select_option('ERROR')
                        assert 'malformed_incompatible_or_processing_error' in page.locator('main').inner_text()
                    if view=='faults':
                        assert '271' in page.locator('main').inner_text()
                        assert 'blanket abstention' in page.locator('main').inner_text()
                        page.screenshot(path=str(output/(label+'-faults.png')),full_page=True)
                page.close()
            # XSS fixture: fake string in ephemeral store only, never saved source/metrics.
            old=store.sections['overview']['data']['evidence'][0]['delivered']
            store.sections['overview']['data']['evidence'][0]['delivered']='<img src=x onerror="window.xss=1">'
            page=browser.new_page();page.goto(base);page.wait_for_selector('h1')
            assert page.locator('main img').count()==0
            assert page.evaluate('window.xss===undefined')
            assert '<img src=x' in page.locator('main').inner_text()
            store.sections['overview']['data']['evidence'][0]['delivered']=old;page.close()
            # Missing section fixture: unavailability displayed, no substitute cards.
            old=store.sections['faults'];store.sections['faults']={'available':False,'error':'Missing or incompatible artifact: test fixture'}
            page=browser.new_page();page.goto(base+'/#faults');page.wait_for_selector('main .error')
            assert page.locator('.stat').count()==0;page.close();store.sections['faults']=old
            browser_version=browser.version;browser.close()
        assert not errors,errors
        assert not external,external
        result=dict(browser_check_version=1,browser='Chromium '+browser_version,
            viewports=[[1440,1000],[390,844]],checks=checks,console_or_page_errors=errors,
            external_requests=external,pagination=True,week8_shift_filter=True,
            status_filters=True,xss_text_inert=True,missing_data_visible=True,
            limitations=['Automated smoke plus visual screenshot inspection; not a screen-reader or full accessibility audit','No Firefox/Safari/Windows browser verification','Screenshots are saved analytical artifacts, never physical evidence'])
        (output/'browser-check.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        print(json.dumps(result,indent=2))
    finally:server.shutdown();server.server_close();thread.join()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path)
    check(parser.parse_args().output)
