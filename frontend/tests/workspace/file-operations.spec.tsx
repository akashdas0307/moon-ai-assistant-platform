import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { WorkspacePanel } from '../../src/components/workspace/WorkspacePanel';
import { useWorkspaceStore } from '../../src/stores/workspaceStore';
import { useToastStore } from '../../src/stores/toastStore';

// Mock dependencies
vi.mock('../../src/services/fileService');
vi.mock('../../src/stores/workspaceStore', () => ({
  useWorkspaceStore: vi.fn(),
}));
vi.mock('../../src/stores/toastStore', () => ({
  useToastStore: vi.fn(),
}));
// Mock FileViewer to avoid complex rendering
vi.mock('../../src/components/workspace/FileViewer', () => ({
  FileViewer: () => <div data-testid="file-viewer">File Viewer</div>,
}));

describe('File Operations Integration', () => {
  const mockCreateNode = vi.fn();
  const mockDeleteNode = vi.fn();
  const mockRenameNode = vi.fn();
  const mockSelectFile = vi.fn();
  const mockAddToast = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock store implementation
    (useWorkspaceStore as any).mockReturnValue({
      files: [
        { path: '/test.txt', name: 'test.txt', type: 'file' },
        { path: '/folder', name: 'folder', type: 'directory' }
      ],
      selectedFile: { path: '/test.txt', name: 'test.txt', content: 'hello' },
      createNode: mockCreateNode,
      deleteNode: mockDeleteNode,
      renameNode: mockRenameNode,
      selectFile: mockSelectFile,
      loadFiles: vi.fn().mockResolvedValue([]),
      openFiles: [],
      activeFilePath: null,
      isLoading: false,
      isLoadingFile: false,
      refreshFiles: vi.fn(),
      openFile: vi.fn(),
    });

    (useToastStore as any).mockReturnValue({
      addToast: mockAddToast,
    });
  });

  it('renders file browser and viewer', () => {
    render(<WorkspacePanel />);
    expect(screen.getByText('test.txt')).toBeInTheDocument();
    expect(screen.getByText('folder')).toBeInTheDocument();
    expect(screen.getByTestId('file-viewer')).toBeInTheDocument();
  });

  it('handle delete shortcut opens dialog', () => {
    render(<WorkspacePanel />);

    // Simulate Delete key
    fireEvent.keyDown(window, { key: 'Delete' });

    expect(screen.getByRole('heading', { name: 'Delete' })).toBeInTheDocument();
    expect(screen.getByText(/Are you sure you want to delete/)).toBeInTheDocument();
  });

  it('handle rename shortcut opens dialog', () => {
    render(<WorkspacePanel />);

    // Simulate F2
    fireEvent.keyDown(window, { key: 'F2' });

    expect(screen.getByRole('heading', { name: 'Rename' })).toBeInTheDocument();
    expect(screen.getByDisplayValue('test.txt')).toBeInTheDocument();
  });

  it('calls deleteNode on confirmation', async () => {
    render(<WorkspacePanel />);

    fireEvent.keyDown(window, { key: 'Delete' });

    const buttons = screen.getAllByText('Delete');
    const confirmButton = buttons.find(b => b.tagName === 'BUTTON');

    if (confirmButton) {
        fireEvent.click(confirmButton);
    } else {
        throw new Error('Confirm button not found');
    }

    await waitFor(() => {
        expect(mockDeleteNode).toHaveBeenCalledWith('/test.txt');
    });

    expect(mockAddToast).toHaveBeenCalledWith('Item deleted', 'success');
  });

  it('calls renameNode on confirmation', async () => {
    render(<WorkspacePanel />);

    fireEvent.keyDown(window, { key: 'F2' });

    const input = screen.getByDisplayValue('test.txt');
    fireEvent.change(input, { target: { value: 'new.txt' } });

    const buttons = screen.getAllByText('Rename');
    const confirmButton = buttons.find(b => b.tagName === 'BUTTON');

    if (confirmButton) {
        fireEvent.click(confirmButton);
    }

    await waitFor(() => {
        expect(mockRenameNode).toHaveBeenCalledWith('/test.txt', '/new.txt');
    });
  });
});
