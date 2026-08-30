function tgNotify(eventName, ok) {
    const color = ok ? '\x1b[32m' : '\x1b[31m';
    console.log(`${color}tg_notify ${eventName}\x1b[0m`);
}

module.exports = { tgNotify };
