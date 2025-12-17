// API configuration
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://web-production-5e612.up.railway.app';

export const api = {
  auth: {
    register: `${API_URL}/api/v1/auth/parent/register`,
    login: `${API_URL}/api/v1/auth/parent/login`,
  },
  children: {
    list: `${API_URL}/api/v1/children/`,
    create: `${API_URL}/api/v1/children/`,
  },
  conversation: {
    message: `${API_URL}/api/v1/conversation/message`,
    list: `${API_URL}/api/v1/conversation/conversations`,
  }
};
