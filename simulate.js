const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const { tgNotify } = require('./integration');

function getArg(name) {
    const index = process.argv.indexOf(name);
    if (index === -1 || !process.argv[index + 1]) {
        throw new Error(`Нужен аргумент ${name}`);
    }
    return process.argv[index + 1];
}

function run(command, args) {
    const result = spawnSync(command, args, { stdio: 'inherit', shell: true });
    if (result.status !== 0) {
        process.exit(result.status ?? 1);
    }
}

function runOffer(args) {
    const result = spawnSync('python', args, { encoding: 'utf8', shell: true });
    if (result.stdout) process.stdout.write(result.stdout);
    if (result.stderr) process.stderr.write(result.stderr);
    const output = `${result.stdout || ''}\n${result.stderr || ''}`;
    if (output.includes('offer: ok')) {
        tgNotify('offer_ok', true);
    } else if (output.includes('offer: no_balance')) {
        tgNotify('offer_no_balance', false);
    } else if (output.includes('offer: already')) {
        tgNotify('offer_already', false);
    }
    if (result.status !== 0) {
        process.exit(result.status ?? 1);
    }
}

const target = getArg('--target');
const workDir = path.join(__dirname, '.simulate');
const projectJson = path.join(workDir, 'project.json');
const orderResponse = path.join(workDir, 'order-response.json');
const filesDir = path.join(workDir, 'files');
const sessionPath = path.join(workDir, 'session.json');

if (!fs.existsSync(sessionPath)) {
    console.error('нет сессии, запустите node auth.js');
    process.exit(1);
}

fs.mkdirSync(workDir, { recursive: true });

run('python', [
    'info2.py',
    '--target', target,
    '--output', projectJson,
    '--output-dir', filesDir,
    '--session', sessionPath,
]);

const project = JSON.parse(fs.readFileSync(projectJson, 'utf8'));
if (project.type !== 'project') {
    console.error(`Тип страницы «${project.type}», нужен project`);
    process.exit(1);
}

run('python', ['ai.py', '--input', projectJson, '--output', orderResponse]);
runOffer([
    'offer.py',
    '--target', target,
    '--order-response', orderResponse,
    '--session', sessionPath,
]);

