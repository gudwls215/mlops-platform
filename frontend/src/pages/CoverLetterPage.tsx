import React from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
} from '@mui/material';
import { Description, Create } from '@mui/icons-material';

const CoverLetterPage: React.FC = () => {
  return (
    <Container maxWidth="md">
      <Typography 
        variant="h3" 
        component="h1" 
        gutterBottom 
        sx={{ textAlign: 'center', mb: 4, fontWeight: 600 }}
      >
        맞춤형 자기소개서
      </Typography>

      <Typography 
        variant="h6" 
        color="text.secondary" 
        sx={{ textAlign: 'center', mb: 6, fontSize: '1.2rem' }}
      >
        지원하고 싶은 회사와 직무에 맞는 자기소개서를 AI가 작성해 드립니다
      </Typography>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <Card sx={{ p: 2 }}>
          <CardContent sx={{ textAlign: 'center' }}>
            <Description sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
              자기소개서 생성
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3, fontSize: '1.1rem' }}>
              이력서와 지원하고자 하는 채용공고를 기반으로
              <br />
              맞춤형 자기소개서를 자동으로 생성해 드립니다.
            </Typography>
            <Button
              variant="contained"
              size="large"
              startIcon={<Create />}
              sx={{ fontSize: '1.1rem', py: 2, px: 4 }}
            >
              자기소개서 작성하기
            </Button>
          </CardContent>
        </Card>

        <Box 
          sx={{ 
            textAlign: 'center', 
            py: 4,
            backgroundColor: 'grey.50',
            borderRadius: 2
          }}
        >
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
            이런 분들께 추천합니다
          </Typography>
          <Box sx={{ mt: 3 }}>
            <Typography variant="body1" sx={{ mb: 1, fontSize: '1.1rem' }}>
              ✓ 자기소개서 작성이 어려우신 분
            </Typography>
            <Typography variant="body1" sx={{ mb: 1, fontSize: '1.1rem' }}>
              ✓ 회사별 맞춤형 자기소개서가 필요하신 분
            </Typography>
            <Typography variant="body1" sx={{ mb: 1, fontSize: '1.1rem' }}>
              ✓ 경력을 효과적으로 어필하고 싶으신 분
            </Typography>
            <Typography variant="body1" sx={{ fontSize: '1.1rem' }}>
              ✓ 시간을 절약하고 싶으신 분
            </Typography>
          </Box>
        </Box>
      </Box>
    </Container>
  );
};

export default CoverLetterPage;