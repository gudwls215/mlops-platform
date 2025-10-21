"""
스케줄링 시스템
정기적인 데이터 처리 작업 스케줄링 및 관리
"""
import asyncio
import schedule
import threading
import time
import logging
from typing import Dict, List, Callable, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from batch_processor_manager import BatchProcessorManager, JobType


class ScheduleFrequency(Enum):
    """스케줄 빈도"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


@dataclass
class ScheduledTask:
    """스케줄된 작업"""
    task_id: str
    name: str
    job_type: JobType
    frequency: ScheduleFrequency
    config: Dict
    next_run: datetime
    last_run: Optional[datetime] = None
    is_active: bool = True
    run_count: int = 0


class DataProcessingScheduler:
    """데이터 처리 스케줄러"""
    
    def __init__(self, batch_manager: BatchProcessorManager):
        """
        스케줄러 초기화
        
        Args:
            batch_manager: 배치 처리 관리자
        """
        self.batch_manager = batch_manager
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.is_running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        
        # 로깅 설정
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 기본 스케줄 설정
        self._setup_default_schedules()
    
    def _setup_default_schedules(self):
        """기본 스케줄 설정"""
        
        # 매시간 텍스트 정제
        self.add_scheduled_task(
            task_id="hourly_text_cleaning",
            name="시간별 텍스트 정제",
            job_type=JobType.TEXT_CLEANING,
            frequency=ScheduleFrequency.HOURLY,
            config={
                'target_table': 'both',
                'days_back': 1,
                'batch_size': 100
            }
        )
        
        # 매일 중복 제거
        self.add_scheduled_task(
            task_id="daily_duplicate_removal",
            name="일일 중복 데이터 제거",
            job_type=JobType.DUPLICATE_REMOVAL,
            frequency=ScheduleFrequency.DAILY,
            config={
                'similarity_threshold': 0.85,
                'keep_strategy': 'most_complete'
            }
        )
        
        # 매일 데이터 검증
        self.add_scheduled_task(
            task_id="daily_data_validation",
            name="일일 데이터 검증",
            job_type=JobType.DATA_VALIDATION,
            frequency=ScheduleFrequency.DAILY,
            config={
                'validation_level': 'standard',
                'target_table': 'both',
                'limit': 500
            }
        )
        
        # 주간 유지보수
        self.add_scheduled_task(
            task_id="weekly_maintenance",
            name="주간 데이터 유지보수",
            job_type=JobType.DATA_MAINTENANCE,
            frequency=ScheduleFrequency.WEEKLY,
            config={
                'cleanup_days_back': 30,
                'optimize_indexes': False  # VACUUM 오류 방지
            }
        )
    
    def add_scheduled_task(self, task_id: str, name: str, job_type: JobType,
                          frequency: ScheduleFrequency, config: Dict,
                          custom_schedule: str = None) -> bool:
        """
        스케줄된 작업 추가
        
        Args:
            task_id: 작업 ID
            name: 작업 이름
            job_type: 작업 타입
            frequency: 스케줄 빈도
            config: 작업 설정
            custom_schedule: 커스텀 스케줄 (cron 형식)
            
        Returns:
            추가 성공 여부
        """
        if task_id in self.scheduled_tasks:
            self.logger.warning(f"이미 존재하는 작업 ID: {task_id}")
            return False
        
        # 다음 실행 시간 계산
        next_run = self._calculate_next_run(frequency, custom_schedule)
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            job_type=job_type,
            frequency=frequency,
            config=config,
            next_run=next_run
        )
        
        self.scheduled_tasks[task_id] = task
        self.logger.info(f"스케줄된 작업 추가: {name} (다음 실행: {next_run})")
        
        return True
    
    def remove_scheduled_task(self, task_id: str) -> bool:
        """
        스케줄된 작업 제거
        
        Args:
            task_id: 작업 ID
            
        Returns:
            제거 성공 여부
        """
        if task_id not in self.scheduled_tasks:
            self.logger.warning(f"존재하지 않는 작업 ID: {task_id}")
            return False
        
        del self.scheduled_tasks[task_id]
        self.logger.info(f"스케줄된 작업 제거: {task_id}")
        
        return True
    
    def _calculate_next_run(self, frequency: ScheduleFrequency, 
                          custom_schedule: str = None) -> datetime:
        """다음 실행 시간 계산"""
        now = datetime.now()
        
        if frequency == ScheduleFrequency.HOURLY:
            # 다음 정시
            return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        
        elif frequency == ScheduleFrequency.DAILY:
            # 다음날 새벽 2시
            next_day = now.replace(hour=2, minute=0, second=0, microsecond=0)
            if now >= next_day:
                next_day += timedelta(days=1)
            return next_day
        
        elif frequency == ScheduleFrequency.WEEKLY:
            # 다음 주 일요일 새벽 3시
            days_until_sunday = (6 - now.weekday()) % 7
            if days_until_sunday == 0 and now.hour >= 3:
                days_until_sunday = 7
            next_sunday = now.replace(hour=3, minute=0, second=0, microsecond=0)
            next_sunday += timedelta(days=days_until_sunday)
            return next_sunday
        
        elif frequency == ScheduleFrequency.MONTHLY:
            # 다음 달 1일 새벽 4시
            if now.month == 12:
                next_month = now.replace(year=now.year + 1, month=1, day=1, 
                                       hour=4, minute=0, second=0, microsecond=0)
            else:
                next_month = now.replace(month=now.month + 1, day=1,
                                       hour=4, minute=0, second=0, microsecond=0)
            return next_month
        
        elif frequency == ScheduleFrequency.CUSTOM and custom_schedule:
            # 커스텀 스케줄 (간단한 파싱)
            # 예: "*/30 * * * *" (30분마다)
            # 실제로는 croniter 라이브러리를 사용하는 것이 좋음
            return now + timedelta(minutes=30)  # 기본값
        
        else:
            # 기본값: 1시간 후
            return now + timedelta(hours=1)
    
    def _update_next_run(self, task: ScheduledTask):
        """다음 실행 시간 업데이트"""
        task.next_run = self._calculate_next_run(task.frequency)
        task.last_run = datetime.now()
        task.run_count += 1
    
    async def check_and_run_scheduled_tasks(self):
        """스케줄된 작업 확인 및 실행"""
        now = datetime.now()
        
        for task_id, task in self.scheduled_tasks.items():
            if not task.is_active:
                continue
            
            # 실행 시간이 되었는지 확인
            if now >= task.next_run:
                self.logger.info(f"스케줄된 작업 실행: {task.name}")
                
                try:
                    # 배치 작업 생성 및 실행 대기열에 추가
                    job_id = self.batch_manager.create_job(task.job_type, task.config)
                    self.logger.info(f"작업 {task.name}에 대한 배치 작업 생성: {job_id}")
                    
                    # 다음 실행 시간 업데이트
                    self._update_next_run(task)
                    
                except Exception as e:
                    self.logger.error(f"스케줄된 작업 실행 중 오류 ({task.name}): {e}")
    
    def start(self):
        """스케줄러 시작"""
        if self.is_running:
            self.logger.warning("스케줄러가 이미 실행 중입니다")
            return
        
        self.is_running = True
        self.logger.info("데이터 처리 스케줄러 시작")
        
        # 별도 스레드에서 스케줄러 실행
        self.scheduler_thread = threading.Thread(target=self._run_scheduler_loop)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
    
    def stop(self):
        """스케줄러 정지"""
        if not self.is_running:
            self.logger.warning("스케줄러가 실행 중이 아닙니다")
            return
        
        self.is_running = False
        self.logger.info("데이터 처리 스케줄러 정지")
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
    
    def _run_scheduler_loop(self):
        """스케줄러 메인 루프"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            while self.is_running:
                # 스케줄된 작업 확인
                loop.run_until_complete(self.check_and_run_scheduled_tasks())
                
                # 배치 매니저의 큐 처리
                loop.run_until_complete(self.batch_manager.process_queue())
                
                # 1분마다 확인
                time.sleep(60)
                
        except Exception as e:
            self.logger.error(f"스케줄러 루프 오류: {e}")
        finally:
            loop.close()
    
    def get_scheduled_tasks_status(self) -> List[Dict]:
        """스케줄된 작업 상태 조회"""
        status_list = []
        
        for task_id, task in self.scheduled_tasks.items():
            status_list.append({
                'task_id': task_id,
                'name': task.name,
                'job_type': task.job_type.value,
                'frequency': task.frequency.value,
                'is_active': task.is_active,
                'next_run': task.next_run,
                'last_run': task.last_run,
                'run_count': task.run_count,
                'config': task.config
            })
        
        return status_list
    
    def activate_task(self, task_id: str) -> bool:
        """작업 활성화"""
        if task_id not in self.scheduled_tasks:
            return False
        
        self.scheduled_tasks[task_id].is_active = True
        self.logger.info(f"작업 활성화: {task_id}")
        return True
    
    def deactivate_task(self, task_id: str) -> bool:
        """작업 비활성화"""
        if task_id not in self.scheduled_tasks:
            return False
        
        self.scheduled_tasks[task_id].is_active = False
        self.logger.info(f"작업 비활성화: {task_id}")
        return True
    
    def print_schedule_report(self):
        """스케줄 리포트 출력"""
        print(f"\n{'='*70}")
        print("데이터 처리 스케줄러 상태")
        print(f"{'='*70}")
        print(f"스케줄러 상태: {'실행 중' if self.is_running else '정지'}")
        print(f"등록된 작업 수: {len(self.scheduled_tasks)}")
        
        if self.scheduled_tasks:
            print(f"\n스케줄된 작업 목록:")
            print(f"{'작업 이름':<25} {'타입':<15} {'빈도':<10} {'다음 실행':<20} {'실행횟수':<8} {'상태'}")
            print("-" * 70)
            
            for task in self.scheduled_tasks.values():
                status = "활성" if task.is_active else "비활성"
                next_run_str = task.next_run.strftime('%m-%d %H:%M') if task.next_run else "미정"
                
                print(f"{task.name:<25} {task.job_type.value:<15} {task.frequency.value:<10} "
                      f"{next_run_str:<20} {task.run_count:<8} {status}")
        
        print(f"{'='*70}\n")


def create_complete_data_processing_system():
    """완전한 데이터 처리 시스템 생성"""
    
    print("완전한 데이터 처리 시스템 초기화 중...")
    
    # 배치 처리 관리자 생성
    batch_config = {
        'max_concurrent_jobs': 2,
        'job_timeout': 1800,  # 30분
        'cleanup_interval': 86400,  # 1일
        'enable_notifications': False
    }
    
    batch_manager = BatchProcessorManager(batch_config)
    
    # 스케줄러 생성
    scheduler = DataProcessingScheduler(batch_manager)
    
    return batch_manager, scheduler


async def run_demo():
    """데모 실행"""
    
    print("데이터 처리 및 저장 시스템 데모 시작...")
    
    # 시스템 생성
    batch_manager, scheduler = create_complete_data_processing_system()
    
    try:
        # 스케줄러 시작
        scheduler.start()
        
        # 현재 스케줄 상태 출력
        scheduler.print_schedule_report()
        batch_manager.print_status_report()
        
        # 즉시 실행할 테스트 작업 추가
        test_job_id = batch_manager.create_job(JobType.FULL_PIPELINE, {
            'similarity_threshold': 0.85,
            'enable_text_cleaning': True,
            'enable_duplicate_removal': True,
            'job_postings': [],  # 실제로는 크롤링 결과
            'cover_letters': []  # 실제로는 크롤링 결과
        })
        
        print(f"\n테스트 작업 생성: {test_job_id}")
        
        # 시스템 모니터링 (30초간)
        start_time = datetime.now()
        timeout = 30
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            # 배치 작업 큐 처리
            await batch_manager.process_queue()
            
            # 상태 체크
            if len(batch_manager.active_jobs) == 0 and len(batch_manager.job_queue) == 0:
                print("모든 작업이 완료되었습니다!")
                break
            
            await asyncio.sleep(2)
        
        # 최종 상태 출력
        print("\n=== 최종 시스템 상태 ===")
        scheduler.print_schedule_report()
        batch_manager.print_status_report()
        
        # 스케줄된 작업 상태
        scheduled_status = scheduler.get_scheduled_tasks_status()
        print("스케줄된 작업 상태:")
        for task_status in scheduled_status:
            print(f"  {task_status['name']}: 다음 실행 {task_status['next_run']}")
        
    except KeyboardInterrupt:
        print("\n시스템 중단됨")
    finally:
        # 정리
        scheduler.stop()
        print("데이터 처리 시스템 정리 완료")


def main():
    """메인 함수"""
    asyncio.run(run_demo())


if __name__ == "__main__":
    main()