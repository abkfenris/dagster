import {gql} from '@apollo/client';
import {ColorsWIP, Group, Mono} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {RunStatusIndicator} from '../runs/RunStatusDots';
import {titleForRun} from '../runs/RunUtils';
import {REPOSITORY_ORIGIN_FRAGMENT} from '../workspace/RepositoryInformation';

import {TICK_TAG_FRAGMENT} from './InstigationTick';
import {InstigationStateFragment} from './types/InstigationStateFragment';
import {RunStatusFragment} from './types/RunStatusFragment';

export const InstigatedRunStatus: React.FC<{
  instigationState: InstigationStateFragment;
}> = ({instigationState}) => {
  if (!instigationState.runs.length) {
    return <span style={{color: ColorsWIP.Gray300}}>None</span>;
  }
  return <RunStatusLink run={instigationState.runs[0]} />;
};

export const RunStatusLink: React.FC<{run: RunStatusFragment}> = ({run}) => (
  <Group direction="row" spacing={4} alignItems="center">
    <RunStatusIndicator status={run.status} />
    <Link to={`/instance/runs/${run.runId}`} target="_blank" rel="noreferrer">
      <Mono>{titleForRun({runId: run.runId})}</Mono>
    </Link>
  </Group>
);

export const RUN_STATUS_FRAGMENT = gql`
  fragment RunStatusFragment on Run {
    id
    runId
    status
  }
`;

export const INSTIGATION_STATE_FRAGMENT = gql`
  fragment InstigationStateFragment on InstigationState {
    id
    name
    instigationType
    status
    repositoryOrigin {
      id
      ...RepositoryOriginFragment
    }
    typeSpecificData {
      ... on SensorData {
        lastRunKey
        lastCursor
      }
      ... on ScheduleData {
        cronSchedule
      }
    }
    runs(limit: 1) {
      id
      ...RunStatusFragment
    }
    status
    ticks(limit: 1) {
      id
      cursor
      ...TickTagFragment
    }
    runningCount
  }
  ${REPOSITORY_ORIGIN_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
  ${TICK_TAG_FRAGMENT}
  ${RUN_STATUS_FRAGMENT}
`;

export const StatusTable = styled.table`
  font-size: 13px;
  border-spacing: 0;

  &&&&& tr {
    box-shadow: none;
  }

  &&&&& tbody > tr > td {
    background: transparent;
    box-shadow: none !important;
    padding: 1px 0;
  }

  &&&&& tbody > tr > td:first-child {
    color: ${ColorsWIP.Gray500};
  }
`;
