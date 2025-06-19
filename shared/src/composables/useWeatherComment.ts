import type { GenerateSettings, GeneratedComment, Location } from '../types';
import { createApiClient } from '../api/client';

export interface UseWeatherCommentOptions {
  apiUrl?: string;
}

export const createWeatherCommentComposable = (options: UseWeatherCommentOptions = {}) => {
  const client = createApiClient(options.apiUrl);
  
  const generateComment = async (
    location: Location,
    settings: Omit<GenerateSettings, 'location'>
  ): Promise<GeneratedComment> => {
    const fullSettings: GenerateSettings = {
      location,
      ...settings,
    };
    
    return client.generateComment(fullSettings);
  };

  const getHistory = async (limit?: number): Promise<GeneratedComment[]> => {
    return client.getHistory(limit);
  };

  const getLocations = async (): Promise<Location[]> => {
    return client.getLocations();
  };

  const getWeatherData = async (locationId: string) => {
    return client.getWeatherData(locationId);
  };

  return {
    generateComment,
    getHistory,
    getLocations,
    getWeatherData,
  };
};