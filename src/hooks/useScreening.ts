import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  getResult,
  runScreen,
  uploadContract,
  type ScreeningResult,
  type UploadResponse,
} from '../api/client';
import type { UploadMeta } from '../lib/mapScreeningResult';

export const screeningKeys = {
  result: (jobId: string) => ['screening', 'result', jobId] as const,
};

export interface ScreeningFlowResult {
  upload: UploadResponse;
  uploadMeta: UploadMeta;
  screening: ScreeningResult;
}

async function runFullScreening(file: File): Promise<ScreeningFlowResult> {
  const upload = await uploadContract(file);
  await runScreen(upload.job_id);
  const screening = await getResult(upload.job_id);
  return {
    upload,
    uploadMeta: {
      filename: upload.filename,
      file_type: upload.file_type,
      text_preview: upload.text_preview,
      char_count: upload.char_count,
    },
    screening,
  };
}

export function useScreeningMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: runFullScreening,
    onSuccess: (data: ScreeningFlowResult) => {
      queryClient.setQueryData(screeningKeys.result(data.upload.job_id), data.screening);
    },
  });
}

export function useScreeningResult(jobId: string | null) {
  return useQuery({
    queryKey: screeningKeys.result(jobId ?? ''),
    queryFn: () => getResult(jobId!),
    enabled: Boolean(jobId),
  });
}
