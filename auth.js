const fs = require('fs');
const path = require('path');

process.loadEnvFile('.env');

const SESSION_PATH = path.join(__dirname, '.simulate', 'session.json');

function hasFlag(name) {
    return process.argv.includes(name);
}

if (!process.env.PUPPETEER_CACHE_DIR) {
    const home = process.env.USERPROFILE || process.env.HOME || '';
    process.env.PUPPETEER_CACHE_DIR = path.join(home, '.cache', 'puppeteer');
}

const config = {
    email: process.env.email,
    password: process.env.password,
    width: 1120,
    height: 840,
    userDataDir: './chrome-profile',
};

const puppeteer = require('puppeteer');
const { sleep, type, findFrameWithSelector, watchCookieBanner, clean } = require('./utils');

async function authorize(page) {
    let trigger = await page.$('#qa-sign-in-href, [data-id="qa-sign-in-href"]');
    if (!trigger) {
        trigger = await page.waitForSelector('a::-p-text(Вход)', { visible: true, timeout: 15000 });
    }
    await trigger.click();
    await sleep(2000);
    await type(page, 'input[name="username"]', config.email);
    await type(page, '#password-field', config.password);
    const { frame, selector } = await findFrameWithSelector(page, ['#js-button']);
    await frame.waitForSelector(selector, { visible: true });
    await frame.click(selector);
    await sleep(1500);
    if (await captchaChecked(page)) {
        console.log('captcha: ok (без челленджа)');
    } else {
        console.log('captcha: есть челлендж, решите в открытом окне');
    }
    const enterButton = await page.waitForSelector('button::-p-text(Войти)', { visible: true, timeout: 3000 }).catch(() => null);
    if (enterButton) {
        await enterButton.click();
    }
    console.log('вход: форма отправлена, заходим на сайт');
}

async function captchaChecked(page) {
    for (const frame of page.frames()) {
        const checked = await frame.$eval('#js-button', (el) => el.getAttribute('aria-checked') === 'true').catch(() => null);
        if (checked) return true;
    }
    return false;
}

async function dumpSession(page) {
    const client = await page.createCDPSession();
    const { cookies: all } = await client.send('Network.getAllCookies');
    const fromPage = await page.cookies();
    const byName = new Map();
    for (const item of [...all, ...fromPage]) {
        const domain = String(item.domain || '');
        if (domain && !domain.includes('fl.ru')) continue;
        byName.set(item.name, item);
    }
    const cookie = [...byName.values()].map((item) => `${item.name}=${item.value}`).join('; ');
    if (!cookie) {
        throw new Error('Не удалось снять куки сессии');
    }
    fs.mkdirSync(path.dirname(SESSION_PATH), { recursive: true });
    fs.writeFileSync(SESSION_PATH, JSON.stringify({ cookie }, null, 2));
    console.log(`session: ${SESSION_PATH}`);
}

async function hasLoginCookies(page) {
    try {
        const fromPage = await page.cookies();
        const names = new Set(fromPage.map((item) => item.name));
        if (names.has('id') && names.has('pwd')) return true;
        const client = await page.createCDPSession();
        const { cookies } = await client.send('Network.getAllCookies');
        const flNames = new Set(
            cookies.filter((item) => String(item.domain || '').includes('fl.ru')).map((item) => item.name),
        );
        return flNames.has('id') && flNames.has('pwd');
    } catch (error) {
        const message = String(error.message || error);
        if (message.includes('Session closed') || message.includes('Target closed') || message.includes('Protocol error')) {
            throw new Error('Окно браузера закрыто до конца авторизации');
        }
        throw error;
    }
}

async function isLoggedInPage(page) {
    if (await hasLoginCookies(page)) return true;
    const uid = await page.$eval('meta[name="current-uid"]', (el) => (el.getAttribute('content') || '').trim()).catch(() => '0');
    if (uid && uid !== '0') return true;
    const signIn = await page.$('a[data-id="qa-head-sign-in"], a[data-id="qa-sign-in-href"], #qa-sign-in-href');
    return !signIn;
}

async function waitForLoginCookies(page, timeout = 300000) {
    const started = Date.now();
    while (true) {
        if (await hasLoginCookies(page)) {
            console.log('вход: авторизованы');
            return;
        }
        if (Date.now() - started >= timeout) break;
        await sleep(1000);
    }
    throw new Error('Нет кук id/pwd, стор не записан');
}

const WORK_LINK = 'a[data-id="qa-head-work"]';

async function openProjects(page) {
    await page.waitForSelector(WORK_LINK, { visible: true });
    await Promise.all([
        page.waitForNavigation({ waitUntil: 'domcontentloaded' }),
        page.click(WORK_LINK),
    ]);
}

(async () => {
    if (hasFlag('--reset')) {
        fs.rmSync(config.userDataDir, { recursive: true, force: true });
        fs.rmSync(path.dirname(SESSION_PATH), { recursive: true, force: true });
    }

    const browser = await puppeteer.launch({
        headless: false,
        userDataDir: config.userDataDir,
        defaultViewport: { width: config.width, height: config.height },
        args: [`--window-size=${config.width},${config.height}`],
    });
    const page = await clean(browser);
    watchCookieBanner(page);
    await page.goto('https://www.fl.ru/');
    await sleep(2000);
    await openProjects(page);

    if (!(await isLoggedInPage(page))) {
        await authorize(page);
        await waitForLoginCookies(page);
    } else {
        console.log('вход: авторизованы');
    }
    await dumpSession(page);
    await browser.close();
})();
