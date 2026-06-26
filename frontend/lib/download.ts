import api from './api';

export async function downloadReport(
  url: string,
  params: Record<string, string>,
  filename: string
): Promise<void> {
  const response = await api.get(url, {
    params,
    responseType: 'blob',
  });
  const contentType = response.headers['content-type'] as string;
  const ext = contentType?.includes('pdf') ? 'pdf' : 'xlsx';
  const blob = new Blob([response.data as BlobPart], { type: contentType });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `${filename}.${ext}`;
  link.click();
  URL.revokeObjectURL(link.href);
}
