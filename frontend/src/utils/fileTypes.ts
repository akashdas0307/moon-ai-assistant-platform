export type FileType = 'code' | 'markdown' | 'image' | 'text' | 'unknown';

const codeExtensions = ['ts', 'tsx', 'js', 'jsx', 'py', 'java', 'cpp', 'c', 'h', 'css', 'scss', 'html', 'json', 'xml', 'yaml', 'yml'];
const markdownExtensions = ['md', 'markdown'];
const imageExtensions = ['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'bmp'];

export function getFileType(filename: string): FileType {
  const ext = filename.split('.').pop()?.toLowerCase();
  if (!ext) return 'unknown';

  if (codeExtensions.includes(ext)) return 'code';
  if (markdownExtensions.includes(ext)) return 'markdown';
  if (imageExtensions.includes(ext)) return 'image';
  if (ext === 'txt') return 'text';
  return 'unknown';
}

export function getLanguageFromExtension(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase();
  const languageMap: Record<string, string> = {
    ts: 'typescript',
    tsx: 'typescript',
    js: 'javascript',
    jsx: 'javascript',
    py: 'python',
    json: 'json',
    html: 'html',
    css: 'css',
    scss: 'scss',
    xml: 'xml',
    yaml: 'yaml',
    yml: 'yaml',
    md: 'markdown',
    txt: 'plaintext',
    c: 'c',
    cpp: 'cpp',
    java: 'java',
    h: 'c', // or cpp
  };
  return languageMap[ext || ''] || 'plaintext';
}
