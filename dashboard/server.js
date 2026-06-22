const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

const app = express();
const PORT = process.env.PORT || 5001;

// CORS 설정 - React Dev Server (보통 5173) 접근 허용
app.use(cors());
app.use(express.json());

// 루트 경로 설정 (위키에이전트 루트 디렉토리)
const ROOT_DIR = path.resolve(__dirname, '..');
const RAW_DIR = path.join(ROOT_DIR, '00_Raw');
const WIKI_DIR = path.join(ROOT_DIR, '10_Wiki');
const META_DIR = path.join(ROOT_DIR, '20_Meta');

// 1. Graph 데이터 가져오기
app.get('/api/graph', (req, res) => {
  const filePath = path.join(META_DIR, 'Graph.json');
  fs.readFile(filePath, 'utf8', (err, data) => {
    if (err) {
      return res.status(500).json({ error: 'Graph.json 로드 실패', details: err.message });
    }
    try {
      res.json(JSON.parse(data));
    } catch (e) {
      res.status(500).json({ error: 'Graph.json 파싱 실패', details: e.message });
    }
  });
});

// 2. Policy 데이터 가져오기
app.get('/api/policy', (req, res) => {
  const filePath = path.join(META_DIR, 'Policy.md');
  fs.readFile(filePath, 'utf8', (err, data) => {
    if (err) {
      return res.status(500).json({ error: 'Policy.md 로드 실패' });
    }
    res.send(data);
  });
});

// 3. Index 데이터 가져오기
app.get('/api/index', (req, res) => {
  const filePath = path.join(META_DIR, 'Index.md');
  fs.readFile(filePath, 'utf8', (err, data) => {
    if (err) {
      return res.status(500).json({ error: 'Index.md 로드 실패' });
    }
    res.send(data);
  });
});

// 4. 위키 마크다운 내용 가져오기
app.get('/api/wiki/*', (req, res) => {
  const relPath = req.params[0];
  const filePath = path.join(ROOT_DIR, relPath);
  
  // 보안 검사: 10_Wiki 하위 혹은 루트 위키 파일만 접근 허용
  if (!filePath.startsWith(WIKI_DIR) && filePath !== path.join(ROOT_DIR, 'P-Reinforce_Skill.md')) {
    return res.status(403).json({ error: '접근이 거부된 디렉토리입니다.' });
  }

  fs.readFile(filePath, 'utf8', (err, data) => {
    if (err) {
      return res.status(404).json({ error: '파일을 찾을 수 없습니다.', path: relPath });
    }
    res.send(data);
  });
});

// 5. 새 원시 데이터 추가 및 강화 프로세스 트리거
app.post('/api/reinforce', (req, res) => {
  const { filename, content } = req.body;
  if (!filename || !content) {
    return res.status(400).json({ error: 'filename과 content가 필요합니다.' });
  }

  // 오늘 날짜 폴더 생성
  const today = new Date().toISOString().split('T')[0];
  const dateFolder = path.join(RAW_DIR, today);
  
  if (!fs.existsSync(dateFolder)) {
    fs.mkdirSync(dateFolder, { recursive: true });
  }

  // 안전한 파일명
  const safeFilename = filename.endsWith('.txt') || filename.endsWith('.md') ? filename : `${filename}.txt`;
  const filePath = path.join(dateFolder, safeFilename);

  // 원시 데이터 파일 저장
  fs.writeFile(filePath, content, 'utf8', (err) => {
    if (err) {
      return res.status(500).json({ error: '원시 파일 저장 실패', details: err.message });
    }

    console.log(`💾 원시 데이터 저장됨: ${filePath}`);

    // reinforce.py 엔진 실행
    const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
    const scriptPath = path.join(ROOT_DIR, 'reinforce.py');
    
    exec(`${pythonCmd} "${scriptPath}"`, { cwd: ROOT_DIR }, (execErr, stdout, stderr) => {
      console.log(`🤖 Engine stdout: ${stdout}`);
      if (stderr) {
        console.error(`🤖 Engine stderr: ${stderr}`);
      }

      if (execErr) {
        return res.status(500).json({ 
          error: 'P-Reinforce 엔진 실행 중 오류 발생', 
          details: execErr.message,
          output: stdout,
          stderr: stderr
        });
      }

      res.json({
        message: '지식 강화 처리가 성공적으로 완료되었습니다.',
        output: stdout,
        file: safeFilename,
        date: today
      });
    });
  });
});

// 서버 실행
app.listen(PORT, () => {
  console.log(`🚀 [P-Reinforce API Server] running on http://localhost:${PORT}`);
});
