const fs = require('fs');
const path = require('path');

process.loadEnvFile('.env');

function getArg(name) {
    const index = process.argv.indexOf(name);
    if (index === -1 || !process.argv[index + 1]) {
        throw new Error(`Нужен аргумент ${name}`);
    }
    return process.argv[index + 1];
}

function hasFlag(name) {
    return process.argv.includes(name);
}

const config = {
    email: process.env.email,
    password: process.env.password,
    width: 1120,
    height: 840,
    userDataDir: './chrome-profile',
    targetOrder: getArg('--target-order'),
    orderResponse: JSON.parse(fs.readFileSync(getArg('--order-response'), 'utf8')),
};

const puppeteer = require('puppeteer');
const { sleep, type, paste, randomDelay, findFrameWithSelector, watchCookieBanner, clean } = require('./utils');

async function authorize(page, config) {
    await page.click('#qa-sign-in-href, [data-id="qa-sign-in-href"]');
    await sleep(2000);
    await type(page, '#ui-input-user-username', config.email);
    await type(page, '#user-password', config.password);
    const { frame, selector } = await findFrameWithSelector(page, ['#js-button']);
    await frame.waitForSelector(selector, { visible: true });
    await frame.click(selector);
    await sleep(1500);
    await page.click('#qa-sign-in-button');
}

async function attachExample(page, frame, filePath) {
    const [chooser] = await Promise.all([
        page.waitForFileChooser(),
        frame.click('#file_select'),
    ]);
    await chooser.accept([path.resolve(filePath)]);
}

async function fillOrderResponse(page, order) {
    await paste(page, '#el-descr', order.summary);
    await sleep(randomDelay(400, 900));
    await type(page, '#el-time_from', String(order.days));
    await sleep(randomDelay(400, 900));
    await type(page, '#el-cost_from', String(order.estimate_cost));

    const examples = (order.examples || []).slice(0, 3);
    if (!examples.length) return;

    await sleep(randomDelay(400, 900));
    await page.click('#work_link_add_example');

    const iframeHandle = await page.waitForSelector('iframe#fupload');
    const uploadFrame = await iframeHandle.contentFrame();
    if (!uploadFrame) throw new Error('iframe#fupload без доступа');

    for (const [index, filePath] of examples.entries()) {
        if (index > 0) {
            await sleep(randomDelay(400, 900));
        }
        await attachExample(page, uploadFrame, filePath);
    }
}

(async () => {
    if (hasFlag('--refresh')) {
        fs.rmSync(config.userDataDir, { recursive: true, force: true });
    }

    const browser = await puppeteer.launch({
        headless: false,
        userDataDir: config.userDataDir,
        defaultViewport: { width: config.width, height: config.height },
        args: [`--window-size=${config.width},${config.height}`],
    });
    const page = await clean(browser);
    watchCookieBanner(page);
    await page.goto(config.targetOrder);
    await sleep(2000);

    if (await page.$('[data-function="document.openChat"]')) {
        console.log('offer: already');
        await browser.close();
        return;
    }

    const replyButton = await page.waitForSelector('a::-p-text(Откликнуться)', { visible: true });
    await replyButton.click();
    await sleep(2000);

    const signInButton = await page.$('#qa-sign-in-href, [data-id="qa-sign-in-href"]');
    if (signInButton) {
        await authorize(page, config);
    }

    if (await page.$('[data-function="document.openChat"]')) {
        console.log('offer: already');
        await browser.close();
        return;
    }

    //TODO V3
    await fillOrderResponse(page, config.orderResponse);
    await sleep(50000);
    await browser.close();
})();
