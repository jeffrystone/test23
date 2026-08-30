async function sleep(time = 5000) {
    await new Promise(resolve => setTimeout(resolve, time));
}

function randomDelay(min, max) {
    return min + Math.random() * (max - min);
}

async function clearHumanLike(page, selector) {
    await page.waitForSelector(selector, { visible: true });
    await page.click(selector);
    await sleep(randomDelay(80, 180));
    await page.keyboard.down('Control');
    await page.keyboard.press('KeyA');
    await page.keyboard.up('Control');
    await sleep(randomDelay(80, 180));
    await page.keyboard.press('Backspace');
}

async function paste(page, selector, text) {
    await clearHumanLike(page, selector);
    await page.keyboard.sendCharacter(String(text));
}

async function type(page, selector, text, { min = 60, max = 180 } = {}) {
    await clearHumanLike(page, selector);
    for (const char of text) {
        await page.keyboard.type(char);
        await sleep(randomDelay(min, max));
    }
}

async function findFrameWithSelector(page, selectors, timeout = 30000) {
    const list = Array.isArray(selectors) ? selectors : [selectors];
    const started = Date.now();
    while (Date.now() - started < timeout) {
        for (const frame of page.frames()) {
            for (const selector of list) {
                const el = await frame.$(selector).catch(() => null);
                if (el) return { frame, selector };
            }
        }
        await sleep(250);
    }

    const urls = page.frames().map((frame) => frame.url());
    throw new Error(`Селектор капчи не найден ни в одном iframe. Фреймы: ${urls.join(' | ')}`);
}

async function clean(browser) {
    const pages = await browser.pages();
    const page = await browser.newPage();
    await Promise.all(pages.map((oldPage) => oldPage.close()));
    return page;
}

async function watchCookieBanner(page) {
    try {
        await page.waitForSelector('#cookie_accept_button', { visible: true });
        await sleep(1000);
        await page.click('#cookie_accept_button');
        console.log('куки приняты');
    } catch {
        // баннер не появился или уже закрыт
    }
}

const EMAIL_CODE_TEXT = 'Введите код из письма для входа';

function isTransientPageError(error) {
    const message = String(error.message || error);
    return (
        message.includes('detached') ||
        message.includes('destroyed') ||
        message.includes('Target closed') ||
        message.includes('Session closed') ||
        message.includes('Protocol error') ||
        message.includes('Execution context')
    );
}

async function hasEmailCodePrompt(page) {
    try {
        return await page.evaluate((text) => Boolean(document.body && document.body.innerText.includes(text)), EMAIL_CODE_TEXT);
    } catch (error) {
        if (isTransientPageError(error)) return null;
        throw error;
    }
}

let emailCodeEnteredPromise = null;
let emailWatchStopped = false;

function stopEmailCodeWatch() {
    emailWatchStopped = true;
}

async function waitForEmailCodeEntered(page) {
    if (emailCodeEnteredPromise) return emailCodeEnteredPromise;
    if ((await hasEmailCodePrompt(page)) !== true) return;
    emailCodeEnteredPromise = (async () => {
        console.log('ждем ввода кода');
        const enterUntil = Date.now() + 300000;
        while (!emailWatchStopped && Date.now() < enterUntil) {
            const state = await hasEmailCodePrompt(page);
            if (state === false) {
                await sleep(800);
                if ((await hasEmailCodePrompt(page)) === false) {
                    console.log('код введен');
                    return;
                }
            }
            await sleep(500);
        }
        if (emailWatchStopped) return;
        throw new Error('Код из письма не введён');
    })();
    return emailCodeEnteredPromise;
}

async function handleEmailCodeIfPresent(page) {
    if ((await hasEmailCodePrompt(page)) !== true) return false;
    await waitForEmailCodeEntered(page);
    return true;
}

async function watchEmailCode(page) {
    const appearUntil = Date.now() + 300000;
    while (!emailWatchStopped && Date.now() < appearUntil) {
        if ((await hasEmailCodePrompt(page)) === true) {
            await waitForEmailCodeEntered(page);
            return;
        }
        await sleep(500);
    }
}

module.exports = {
    sleep,
    type,
    paste,
    clearHumanLike,
    randomDelay,
    findFrameWithSelector,
    watchCookieBanner,
    hasEmailCodePrompt,
    watchEmailCode,
    handleEmailCodeIfPresent,
    waitForEmailCodeEntered,
    stopEmailCodeWatch,
    clean,
};
